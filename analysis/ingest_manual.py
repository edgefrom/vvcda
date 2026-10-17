"""Inventory/import manual downloads without overwriting raw evidence.

Usage: python -X utf8 analysis/ingest_manual.py [--apply]
Archives originals only after canonical copies and a manifest have been verified.
Phase is inferred from export filenames with provenance, never folder numbers.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, re, shutil, zipfile
import xlrd

ROOT=Path(__file__).resolve().parents[1]
INBOX=ROOT/'manual'
def digest(data): return hashlib.sha256(data).hexdigest()
def contained(path,base):
    path=path.resolve(); base=base.resolve()
    if path!=base and base not in path.parents: raise ValueError(f'Unsafe path: {path}')
    return path
def phase_hint(path):
    """Keep phase identity when deduplicating even if two rounds have equal cells."""
    normalized=str(path).replace('\\','/')
    canonical=re.search(r'(formal|practice)/round-(\d+)(?:/|$)',normalized)
    if canonical: return f'{canonical[1]}/round-{int(canonical[2]):02d}'
    match=re.fullmatch(r'results-r(\d+)(?: \(\d+\))?',path.stem,re.I)
    practice=re.fullmatch(r'results-pr(\d+)(?: \(\d+\))?',path.stem,re.I)
    if match: return f'formal/round-{int(match[1]):02d}'
    if practice: return f'practice/round-{int(practice[1]):02d}'
    if path.stem.startswith('results-ir') or 'reference-initial-unassigned/' in normalized: return 'reference-initial-unassigned'
    return 'unclassified'
def book_info(path):
    if path.suffix.lower()=='.xls':
        book=xlrd.open_workbook(path)
        sheets=[(s.name,[s.row_values(i) for i in range(s.nrows)]) for s in book.sheets()]
    elif path.suffix.lower()=='.xlsx':
        import openpyxl
        book=openpyxl.load_workbook(path,read_only=True,data_only=True)
        sheets=[(s.title,[list(row) for row in s.iter_rows(values_only=True)]) for s in book]
        book.close()
    else: return {}
    normalized=[]
    for name,rows in sheets:
        normalized_rows=[]
        for row in rows:
            nr=[]
            for x in row:
                if x is None: x=''
                if isinstance(x,(int,float)) and not isinstance(x,bool): x=float(x)
                elif not isinstance(x,(str,bool,float)): x=str(x)
                nr.append(x)
            while nr and nr[-1]=='': nr.pop()
            normalized_rows.append(nr)
        while normalized_rows and not normalized_rows[-1]: normalized_rows.pop()
        normalized.append([name,normalized_rows])
    first=sheets[0][1]
    roster=sorted(str(v).strip() for v in first[1][1:] if str(v or '').strip()) if len(first)>1 else []
    return {'semantic_sha256':digest(json.dumps(normalized,ensure_ascii=False,allow_nan=False).encode()),
            'roster_sha256':digest(json.dumps(roster,ensure_ascii=False).encode()),
            'roster':roster,'title':str(first[0][0]),'sheet_shapes':[(n,len(rs),max(map(len,rs),default=0)) for n,rs in sheets]}
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--apply',action='store_true'); args=parser.parse_args()
    candidates=sorted(p for p in INBOX.rglob('*') if p.is_file() and p.name not in ['README.md','AGENTS.md'])
    if not candidates: print('No new manual files.'); return
    batch=datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    archive=contained(ROOT/'archive/manual-imports'/batch,ROOT)
    manifest_path=ROOT/'data/intake'/f'{batch}.json'
    existing_bytes={}; existing_sem={}; existing_parse_errors=[]
    for p in sorted((ROOT/'data/raw').rglob('*')):
        if not p.is_file(): continue
        existing_bytes.setdefault((phase_hint(p),digest(p.read_bytes())),str(p.relative_to(ROOT)))
        if p.suffix.lower() in ['.xls','.xlsx']:
            try: info=book_info(p); existing_sem.setdefault((phase_hint(p),info['semantic_sha256']),str(p.relative_to(ROOT)))
            except Exception as e: existing_parse_errors.append({'source':str(p.relative_to(ROOT)),'error':str(e)})
    rows=[]; zip_details=[]
    known_download_hashes={digest(p.read_bytes()) for p in candidates if p.suffix.lower()!='.zip'}
    for p in candidates:
        raw=p.read_bytes(); h=digest(raw)
        row={'original_path':str(p.relative_to(ROOT)),'sha256':h,'bytes':len(raw),
             'original_mtime':datetime.datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
             'archive_path':str((archive/p.relative_to(INBOX)).relative_to(ROOT))}
        if p.suffix.lower()=='.zip':
            with zipfile.ZipFile(p) as z:
                members=[{'name':m.filename,'sha256':digest(z.read(m)),'bytes':m.file_size} for m in z.infolist() if not m.is_dir()]
            existing_hashes={h for _,h in existing_bytes}
            missing=[m['name'] for m in members if m['sha256'] not in known_download_hashes and m['sha256'] not in existing_hashes]
            row.update(kind='source_archive',canonical_path=None,zip_members=members,unrepresented_members=missing)
            if missing: raise ValueError(f'ZIP contains unrepresented files; inspect before import: {missing}')
            zip_details.append({'original_path':row['original_path'],'member_count':len(members),'unrepresented':missing})
        else:
            try: info=book_info(p)
            except Exception as e: info={'parse_error':str(e)}
            row.update(info)
            kind=phase_hint(p) if info and 'parse_error' not in info else 'unclassified'
            row['kind']=kind
            row['classification_basis']='export_filename_and_workbook_content; folder_numbers_not_used; reference_initial_not_assigned_to_our_team'
            canonical=existing_bytes.get((kind,h)) or existing_sem.get((kind,info.get('semantic_sha256')))
            if canonical:
                row['deduplication']='existing_content'
            else:
                stem=('cohort-'+info['roster_sha256'][:12]+'-'+info['semantic_sha256'][:8]) if 'roster_sha256' in info else p.stem+'-'+h[:8]
                canonical=str(Path('data/raw')/kind/(stem+p.suffix.lower()))
                row['deduplication']='new_content'
            row['canonical_path']=canonical
            existing_bytes[(kind,h)]=canonical
            if 'semantic_sha256' in info: existing_sem[(kind,info['semantic_sha256'])]=canonical
        rows.append(row)
    manifest={'batch':batch,'status':'planned','files':rows,'zip_details':zip_details,'existing_raw_parse_errors':existing_parse_errors,
              'policy':'Original bytes preserved in archive; canonical raw never overwritten; duplicate links recorded.'}
    counts={k:sum(r['kind']==k for r in rows) for k in sorted(set(r['kind'] for r in rows))}
    print(json.dumps({'files':len(rows),'kinds':counts,'new_canonical':sum(r.get('deduplication')=='new_content' for r in rows),
                      'duplicate_links':sum(r.get('deduplication')=='existing_content' for r in rows),'zip':zip_details,
                      'our_new_files':[(r['original_path'],r.get('canonical_path')) for r in rows if '维维一笑队' in r.get('roster',[]) and r.get('deduplication')=='new_content']},ensure_ascii=False,indent=2))
    if not args.apply: return
    manifest_path.parent.mkdir(parents=True,exist_ok=True)
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in rows:
        src=contained(ROOT/r['original_path'],INBOX)
        if r.get('deduplication')=='new_content':
            target=contained(ROOT/r['canonical_path'],ROOT/'data/raw')
            target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists(): raise FileExistsError(target)
            shutil.copy2(src,target)
            assert digest(target.read_bytes())==r['sha256']
    for r in rows:
        src=contained(ROOT/r['original_path'],INBOX)
        target=contained(ROOT/r['archive_path'],archive)
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists(): raise FileExistsError(target)
        shutil.move(str(src),str(target))
        assert digest(target.read_bytes())==r['sha256']
    for d in sorted((p for p in INBOX.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):
        contained(d,INBOX)
        if not any(d.iterdir()): d.rmdir()
    manifest['status']='complete_verified'
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Completed:',str(manifest_path.relative_to(ROOT)))
if __name__=='__main__': main()

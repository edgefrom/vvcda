"""Read-only handoff checks: provenance, frozen decisions, evidence and accounts."""
from pathlib import Path
import csv,hashlib,json,sys
from ingest_manual import book_info
from results_reader import read_result

ROOT=Path(__file__).resolve().parents[1]
def locate(rel):
    p=(ROOT/str(rel).replace('\\','/')).resolve()
    if ROOT!=p and ROOT not in p.parents: raise ValueError('Source outside workspace')
    return p
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().lower()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    counts={'archived_manual_originals':0,'canonical_byte_matches':0,'canonical_semantic_matches':0,'frozen_files':0,'screenshots':0,'legacy_files':0,'legacy_cache_entries_intentionally_excluded':0,'formal_cohorts':0,'formal_companies':0}
    for manifest in sorted((ROOT/'data/intake').glob('*.json')):
        m=read(manifest)
        if m['status']!='complete_verified': raise AssertionError(f'Incomplete intake: {manifest.name}')
        for r in m['files']:
            assert sha(locate(r['archive_path']))==r['sha256'].lower(),r['archive_path']
            counts['archived_manual_originals']+=1
            if r.get('canonical_path'):
                p=locate(r['canonical_path'])
                if sha(p)==r['sha256'].lower(): counts['canonical_byte_matches']+=1
                else:
                    assert book_info(p)['semantic_sha256']==r['semantic_sha256'],r['canonical_path']
                    counts['canonical_semantic_matches']+=1
    snap=ROOT/'archive/decision-snapshots/formal-round-01/manifest.json'
    for r in read(snap)['files']:
        assert sha(locate(r['snapshot']))==r['sha256'].lower(),r['snapshot']
        # These six source files remain frozen in this version too.
        assert sha(locate(r['source']))==r['sha256'].lower(),r['source']
        counts['frozen_files']+=1
    for index in (ROOT/'data/evidence').glob('*/index.json'):
        for r in read(index):
            assert sha(index.parent/r['file'])==r['sha256'].lower(),r['file']
            counts['screenshots']+=1
    legacy=ROOT/'archive/legacy-model-2026-10-17'
    with (legacy/'move-manifest.csv').open(encoding='utf-8-sig',newline='') as fp:
        for r in csv.DictReader(fp):
            p=legacy/r['OriginalPath'].replace('\\','/')
            # The historical manifest also recorded compiled local caches.
            # Preserve that manifest, but do not require ignored garbage.
            if '__pycache__' in p.parts or '.pytest_cache' in p.parts or p.suffix in {'.pyc','.pyo'}:
                counts['legacy_cache_entries_intentionally_excluded']+=1
                continue
            assert sha(p)==r['SHA256'].lower(),r['OriginalPath']
            counts['legacy_files']+=1
    d=read(ROOT/'analysis/formal-round-01/diagnosis.json')
    for rel,h in d['source_hashes'].items(): assert sha(locate(rel))==h.lower(),rel
    assert abs(sum(x['amount'] for x in d['net_bridge'])-d['our_result']['finance']['net'])<1e-6
    warnings=[]; own=None; cohorts=set()
    for p in sorted((ROOT/'data/raw/formal/round-01').glob('*.xls')):
        c=read_result(p,'formal-01',ROOT)
        assert c['cohort'] not in cohorts,'Duplicate formal cohort'
        cohorts.add(c['cohort']); counts['formal_cohorts']+=1;counts['formal_companies']+=len(c['records'])
        for e in c['reconciliation_errors']:
            assert e['check'] in {'product_cost','advertising','channels'},e
            warnings.append({'source':c['source'],**e})
        if '维维一笑队' in c['roster']:
            assert not c['reconciliation_errors']
            own=next(r for r in c['records'] if r['team']=='维维一笑队')
    assert own is not None
    for k,v in own['finance'].items():
        expected=d['our_result']['finance'][k]
        assert v==expected or (v is not None and expected is not None and abs(v-expected)<1e-8),k
    assert own['stock_rank']==4 and own['net_rank']==2
    expected={(str(e['source']).replace('\\','/'),e['team'],e['check']) for e in d['raw_accounting_reconciliation_errors'] if 'formal' in e['source']}
    actual={(e['source'],e['team'],e['check']) for e in warnings}
    assert expected==actual,'Cross-table warning set changed; investigate'
    print(json.dumps({'status':'PASS','counts':counts,'known_formal_cross_table_warnings':len(warnings),'own_cohort_all_checks_pass':True,'note':'Provenance and accounting verified; this does not validate causal demand or stock predictions.'},ensure_ascii=False,indent=2))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()

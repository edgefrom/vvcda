from pathlib import Path
import hashlib, json
from collections import Counter
import xlrd

files = sorted(Path('data/raw').glob('results-*/*.xls'))
print('FILES', len(files))
hits = []
for p in files:
    b = xlrd.open_workbook(p)
    s = b.sheet_by_index(0)
    teams = [(c, s.cell_value(1,c)) for c in range(s.ncols) if '维维' in str(s.cell_value(1,c))]
    if teams:
        hits.append(p)
        print('HIT', p, b.sheet_names(), s.nrows, s.ncols, teams)
seen = {}
allrows = []
for p in files:
    s = xlrd.open_workbook(p).sheet_by_index(0)
    digest = hashlib.sha256(json.dumps([s.row_values(i) for i in range(s.nrows)],ensure_ascii=False).encode()).hexdigest()
    if digest in seen:
        print('DUPLICATE',p,seen[digest])
        continue
    seen[digest] = str(p)
    names = [(c,str(s.cell_value(1,c)).strip()) for c in range(1,s.ncols) if str(s.cell_value(1,c)).strip()]
    for idx,(base,name) in enumerate(names):
        fc=idx+1
        assert s.cell_value(206,fc)==name
        row={'file':str(p),'round':p.parent.name,'name':name}
        for r in [208,209,210,213,217,220,221,222,223,224,225,226,229,231,238,249,260,273,274,275,289]:
            row[str(r)]=s.cell_value(r,fc)
        for market,pr,sr in [('EU',3,11),('AS',42,50)]:
            cols=[c for c in range(base,base+6) if isinstance(s.cell_value(pr,c),(int,float)) and s.cell_value(pr,c)>0]
            row[market+'qty']=sum(s.cell_value(sr,c) for c in cols)
            row[market+'n']=len(cols)
        allrows.append(row)
print('UNIQUE',len(seen),'COMPANIES',Counter(r['round'] for r in allrows))
for turn in ['results-1','results-2']:
    rows=[r for r in allrows if r['round']==turn]
    print('SUMMARY',turn,'profitable',sum(r['238']>0 for r in rows),'active',sum(r['208']>0 for r in rows))
    print('TOP', sorted(rows,key=lambda r:r['274'],reverse=True)[:5])
for p in hits[:2]:
    s = xlrd.open_workbook(p).sheet_by_index(0)
    print('\nSOURCE', p)
    for i in [0,1,125]: print(i,s.row_values(i))
    for i in list(range(3,40))+list(range(42,79)):
        if str(s.cell_value(i,0)).strip(): print(i,s.cell_value(i,0),s.row_values(i)[19:25])
    for i in list(range(208,239))+list(range(270,286))+[289]:
        if str(s.cell_value(i,0)).strip(): print(i,s.cell_value(i,0),s.cell_value(i,4))
    for mk,sr in [('EU',11),('AS',50)]:
        print('MARKET',mk,sum(v for v in s.row_values(sr)[1:] if isinstance(v,(int,float))))
    for r in sorted([r for r in allrows if r['file']==str(p)],key=lambda r:r['274'],reverse=True): print('PEER',r)
Path('analysis/practice_summary.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2),encoding='utf8')

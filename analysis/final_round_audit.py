"""Read original practice sheets without importing the legacy model."""
from pathlib import Path
import json, hashlib
import xlrd

ROOT = Path(__file__).resolve().parents[1]
records=[]
seen=set()
for path in sorted((ROOT/'data/raw').glob('results-*/*.xls')):
    sheet=xlrd.open_workbook(path).sheet_by_index(0)
    digest=hashlib.sha256(json.dumps([sheet.row_values(i) for i in range(sheet.nrows)],ensure_ascii=False).encode()).hexdigest()
    if digest in seen: continue
    seen.add(digest)
    teams=[(c,str(sheet.cell_value(1,c)).strip()) for c in range(1,sheet.ncols) if str(sheet.cell_value(1,c)).strip()]
    for idx,(base,name) in enumerate(teams):
        fc=idx+1
        assert sheet.cell_value(206,fc)==name
        record={'source':str(path.relative_to(ROOT)),'round':path.parent.name,'team':name,
                'finance':{str(sheet.cell_value(r,0)).strip()+'_'+str(r):sheet.cell_value(r,fc) for r in [208,209,213,217,220,221,222,223,224,225,226,227,229,231,234,235,236,237,238,249,260,273,274,281,282,284,285,289]},'products':[]}
        for market,offset in [('EU',0),('AS',39)]:
            for col in range(base,min(base+6,sheet.ncols)):
                price=sheet.cell_value(3+offset,col)
                if not isinstance(price,(int,float)) or price<=0: continue
                record['products'].append({'market':market,'slot':col-base+1,'price':price,
                    'quantities':[sheet.cell_value(r+offset,col) for r in [6,7,8,9]],
                    'quantity':sheet.cell_value(11+offset,col),
                    'ads':sheet.cell_value(25+offset,col),'channels':sheet.cell_value(26+offset,col),
                    'performance':sheet.cell_value(29+offset,col),'battery':sheet.cell_value(30+offset,col),
                    'features':[sheet.cell_value(r+offset,col) for r in range(32,37)],
                    'style':sheet.cell_value(37+offset,col),'unit_cost':sheet.cell_value(39+offset,col)})
        records.append(record)
out=ROOT/'analysis/final-practice-audit.json'
out.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
for turn in ['results-1','results-2']:
    group=[r for r in records if r['round']==turn and ('(13)' in r['source'] if turn=='results-1' else '(10)' in r['source'])]
    for r in sorted(group,key=lambda r:r['finance']['股票价格, €_274'],reverse=True):
        f=r['finance']
        print(json.dumps({'round':turn,'team':r['team'],'stock':round(f['股票价格, €_274'],2),'net':round(f['本回合利润_238']),
              'RD':f['研发投资_226'],'fixed':round(f['固定成本合计_229']),'forecast_error':f['销售预测误差，％_273'],
              'products':r['products']},ensure_ascii=False))

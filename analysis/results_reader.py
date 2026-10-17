"""CESIM 290-row result export reader with explicit label and accounting checks.

No fitted legacy model is used. Unsupported layouts fail instead of shifting rows.
Missing values stay None. 'x' product features stay boolean True.
"""
from pathlib import Path
import hashlib,json,math
import xlrd

FIN={208:'product_revenue',209:'service_revenue',210:'revenue',213:'product_cost',214:'service_cost',215:'variable_cost',217:'gross_profit',
220:'admin',221:'line',222:'ads',223:'channels',224:'warranty',225:'repair_quality',226:'rd',227:'reports',229:'fixed',231:'ebit',
234:'interest_income',235:'interest_expense',236:'pretax',237:'tax',238:'net',248:'ar',249:'cash',251:'assets',255:'capital',256:'retained',257:'current_profit',258:'equity',260:'debt',261:'ap',262:'liabilities',263:'liabilities_equity',
270:'gross_margin_pct',271:'return_on_sales_pct',272:'net_margin_pct',273:'forecast_error_pct',274:'stock',275:'cumulative_profit',281:'next_performance',282:'next_battery',284:'performance_technology',285:'battery_technology',289:'platform_forecast_net'}
LABELS={3:'定价, €',6:'普通消费者',7:'高端消费者',8:'企业用户',9:'高端企业用户',11:'销售合计',25:'广告费',26:'渠道投资',29:'机身轻薄度',30:'电池寿命',32:'高像素',33:'额外存储',34:'高级屏幕',35:'导航功能',36:'安全功能',37:'外观',39:'单位可变成本, €',
42:'定价, €',50:'销售合计',78:'单位可变成本, €',84:'产品认知',90:'购买意向',96:'销售',208:'产品销售额',209:'维修收入',210:'销售合计',213:'产品',217:'毛利润',220:'管理成本',221:'生产线成本',222:'广告费',223:'渠道投资',224:'质保',225:'维修质量投资',226:'研发投资',227:'市场调研',229:'固定成本合计',231:'营业利润',238:'本回合利润',249:'现金及等价物',256:'留存盈余',274:'股票价格, €',289:'预估净收入'}
FEATURES=['camera','storage','screen','navigation','security']
def number(v,required=False):
    if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v): return float(v)
    if required: raise ValueError(f'Expected finite numeric cell, got {v!r}')
    return None
def close(a,b,label,errors):
    delta=a-b
    if abs(delta)>max(1e-6,1e-9*max(abs(a),abs(b))): errors.append({'check':label,'left':a,'right':b,'delta':delta})
def read_result(path,phase,root):
    s=xlrd.open_workbook(path).sheet_by_index(0)
    if s.nrows!=290: raise ValueError(f'Unsupported layout {path}: {s.nrows} rows')
    for row,expected in LABELS.items():
        if str(s.cell_value(row,0)).strip()!=expected: raise ValueError(f'Label mismatch {path} row {row+1}: {s.cell_value(row,0)!r}')
    teams=[(c,str(s.cell_value(1,c)).strip()) for c in range(1,s.ncols) if str(s.cell_value(1,c)).strip()]
    roster=sorted(name for _,name in teams)
    cohort=hashlib.sha256(json.dumps(roster,ensure_ascii=False).encode()).hexdigest()
    records=[]; all_errors=[]
    for idx,(base,name) in enumerate(teams):
        fc=idx+1
        for header in [125,142,174,206]:
            assert str(s.cell_value(header,fc)).strip()==name,(path,header,fc,name)
        finance={key:number(s.cell_value(row,fc),required=row!=273) for row,key in FIN.items()}
        r={'source':path.relative_to(root).as_posix(),'phase':phase,'cohort':cohort,'team':name,'financial_column_1based':fc+1,
           'finance':finance,'products':[],'services':{}}
        for market,off,funnel in [('EU',0,0),('AS',39,19)]:
            for col in range(base,base+6):
                price=number(s.cell_value(3+off,col))
                if price is None or price<=0: continue
                flags={}
                for j,key in enumerate(FEATURES):
                    value=str(s.cell_value(32+off+j,col)).strip()
                    if value not in ['','x','X']: raise ValueError(f'Unrecognized feature marker {value}')
                    flags[key]=value.lower()=='x'
                n=lambda row:number(s.cell_value(row,col),required=True)
                r['products'].append({'market':market,'slot':col-base+1,'name':str(s.cell_value(83+funnel,col)),
                    'source_column_1based':col+1,'price':price,'quantity':[n(row+off) for row in range(6,10)],'total_quantity':n(11+off),
                    'channel_sales':[n(row+off) for row in range(14,17)],'segment_share_pct':[n(row+off) for row in range(19,23)],
                    'ads':n(25+off),'channels':n(26+off),'performance':n(29+off),'battery':n(30+off),'features':flags,'style':str(s.cell_value(37+off,col)),
                    'unit_cost':n(39+off),'awareness':[n(row+funnel) for row in range(85,89)],'intent':[n(row+funnel) for row in range(91,95)],'funnel_sales':[n(row+funnel) for row in range(97,101)]})
            off_service=0 if market=='EU' else 6
            r['services'][market]={key:number(s.cell_value(row+off_service,fc),required=True) for row,key in [(127,'markup_pct'),(128,'quantity'),(129,'revenue'),(130,'cost'),(131,'gross')]}
        errors=[]; f=finance; prods=r['products']
        for p in prods:
            close(sum(p['quantity']),p['total_quantity'],'product_segment_sum',errors)
            close(sum(p['channel_sales']),p['total_quantity'],'product_channel_sum',errors)
            close(sum(p['funnel_sales']),p['total_quantity'],'product_funnel_sum',errors)
        close(sum(p['price']*p['total_quantity'] for p in prods),f['product_revenue'],'product_revenue',errors)
        close(sum(p['unit_cost']*p['total_quantity'] for p in prods),f['product_cost'],'product_cost',errors)
        close(sum(p['ads'] for p in prods),f['ads'],'advertising',errors)
        close(sum(p['channels'] for p in prods),f['channels'],'channels',errors)
        close(f['product_revenue']+f['service_revenue'],f['revenue'],'revenue_sum',errors)
        close(f['product_cost']+f['service_cost'],f['variable_cost'],'variable_sum',errors)
        close(f['revenue']-f['variable_cost'],f['gross_profit'],'gross_profit',errors)
        close(sum(f[k] for k in ['admin','line','ads','channels','warranty','repair_quality','rd','reports']),f['fixed'],'fixed_cost_sum',errors)
        close(f['gross_profit']-f['fixed'],f['ebit'],'ebit',errors)
        close(f['ebit']+f['interest_income']-f['interest_expense'],f['pretax'],'pretax',errors)
        close(f['pretax']-f['tax'],f['net'],'net',errors)
        close(f['ar']+f['cash'],f['assets'],'assets',errors)
        close(f['capital']+f['retained']+f['current_profit'],f['equity'],'equity',errors)
        close(f['equity']+f['debt']+f['ap'],f['assets'],'balance',errors)
        r['reconciliation_errors']=errors
        all_errors.extend([{'team':name,**e} for e in errors]); records.append(r)
    market={m:{'quantity':sum(p['total_quantity'] for r in records for p in r['products'] if p['market']==m),
               'segments':[sum(p['quantity'][j] for r in records for p in r['products'] if p['market']==m) for j in range(4)],
               'active_companies':sum(any(p['market']==m for p in r['products']) for r in records),
               'active_product_listings':sum(p['market']==m for r in records for p in r['products'])} for m in ['EU','AS']}
    for r in records:
        r['stock_rank']=1+sum(x['finance']['stock']>r['finance']['stock']+1e-9 for x in records)
        r['net_rank']=1+sum(x['finance']['net']>r['finance']['net']+1e-9 for x in records)
    return {'source':path.relative_to(root).as_posix(),'phase':phase,'cohort':cohort,'roster':roster,'markets':market,'records':records,'reconciliation_errors':all_errors}

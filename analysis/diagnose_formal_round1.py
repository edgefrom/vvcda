"""Round-1 diagnosis from raw exports. Decompositions are accounting, not causal estimates."""
from pathlib import Path
import json,statistics,hashlib,sys,csv
from results_reader import read_result

ROOT=Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding='utf-8')
OUT=ROOT/'analysis/formal-round-01'; OUT.mkdir(exist_ok=True)
formal=[read_result(p,'formal-01',ROOT) for p in sorted((ROOT/'data/raw/formal/round-01').glob('*.xls'))]
practice=[read_result(p,'practice-01',ROOT) for p in sorted((ROOT/'data/raw/results-1').glob('*.xls'))]
assert len({x['cohort'] for x in formal})==len(formal),'Duplicate cohort exports need explicit resolution'
allrows=[r for c in formal for r in c['records']]
errors=[{'source':c['source'],**e} for c in formal+practice for e in c['reconciliation_errors']]
# Some original foreign exports have zero unit-cost cells or product/financial
# marketing totals that disagree. Keep these visible; never silently repair them.
# Their internally reconciled financial totals can still support descriptive stats.
fatal_errors=[e for e in errors if e['check'] not in {'product_cost','advertising','channels'}]
assert not fatal_errors,fatal_errors
cohort=next(c for c in formal if '维维一笑队' in c['roster'])
assert not cohort['reconciliation_errors'],cohort['reconciliation_errors']
ours=next(r for r in cohort['records'] if r['team']=='维维一笑队')
oldcohort=next(c for c in practice if c['cohort']==cohort['cohort'])
old=next(r for r in oldcohort['records'] if r['team']==ours['team'])
plan=json.loads((ROOT/'analysis/round1_plan.json').read_text(encoding='utf-8'))
oldcalc=json.loads((ROOT/'analysis/round1-scenario-results.json').read_text(encoding='utf-8'))
f=ours['finance']; products=ours['products']; proposals=plan['products']
comparison=[]; volume_effect=0; cost_effect=0; expected_warranty_actual_q=0
for proposal,actual in zip(proposals,products):
    assert proposal['slot']==actual['slot']
    q0=sum(proposal['quantity']); q=actual['total_quantity']
    cm0=proposal['price']-proposal['unit_cost_assumed']-proposal['warranty_per_unit_assumed']
    ve=(q-q0)*cm0; ce=q*(proposal['unit_cost_assumed']-actual['unit_cost'])
    volume_effect+=ve; cost_effect+=ce; expected_warranty_actual_q+=q*proposal['warranty_per_unit_assumed']
    checks={k:{'recommended':proposal[k],'actual':actual[k],'same':proposal[k]==actual[k]} for k in ['style','performance','battery','features','price']}
    checks['ads']={'recommended':sum(proposal['ads']),'actual':actual['ads'],'same':sum(proposal['ads'])==actual['ads']}
    checks['channels']={'recommended':sum(proposal['channels']),'actual':actual['channels'],'same':sum(proposal['channels'])==actual['channels']}
    comparison.append({'slot':actual['slot'],'actual_name':actual['name'],'checks':checks,'recommended_forecast':proposal['quantity'],'actual_sales':actual['quantity'],
                       'forecast_total':q0,'actual_total':q,'achievement_pct':q/q0*100,'volume_profit_effect':ve,'unit_cost_profit_effect':ce,
                       'actual_gross_before_warranty':q*(actual['price']-actual['unit_cost'])})
service_gross=f['service_revenue']-f['service_cost']
base=oldcalc['base_with_repair']; fixed_ex_w=f['fixed']-f['warranty']
bridge=[{'item':'建议基准净利润','amount':base['net']},
        {'item':'欧洲1销量未达建议预测','amount':comparison[0]['volume_profit_effect']},
        {'item':'欧洲2销量未达建议预测','amount':comparison[1]['volume_profit_effect']},
        {'item':'实际单位产品成本与假设差异','amount':cost_effect},
        {'item':'质保单位假设残差','amount':expected_warranty_actual_q-f['warranty']},
        {'item':'固定费用差异（不含质保）','amount':oldcalc['fixed_excluding_warranty']-fixed_ex_w},
        {'item':'维修毛利高于假设','amount':service_gross-(base['repair_rev']-base['repair_cost'])},
        {'item':'实际净利息收入','amount':f['interest_income']-f['interest_expense']},
        {'item':'未发生基准假设所得税','amount':base['tax']-f['tax']}]
assert abs(sum(x['amount'] for x in bridge)-f['net'])<1e-6
market=cohort['markets']; forecast_market=plan['assumptions']['europe_market_approx']; actual_market=market['EU']['segments']
forecast=[sum(p['quantity'][j] for p in proposals) for j in range(4)]
actual=[sum(p['quantity'][j] for p in products) for j in range(4)]
market_volume_effect=[forecast[j]*(actual_market[j]/forecast_market[j]-1) for j in range(4)]
share_effect=[actual[j]-forecast[j]-market_volume_effect[j] for j in range(4)]
funnel=[]
for p in products:
    for j,seg in enumerate(['普通消费者','高端消费者','企业用户','高端企业用户']):
        awareness,intent,sales=p['awareness'][j],p['intent'][j],p['quantity'][j]
        funnel.append({'slot':p['slot'],'segment':seg,'awareness':awareness,'intent':intent,'sales':sales,
                       'awareness_to_intent_pct':100*intent/awareness if awareness else None,'intent_to_sales_pct':100*sales/intent if intent else None})
global_stats={'cohorts':len(formal),'companies':len(allrows),'profitable':sum(r['finance']['net']>0 for r in allrows),
              'median_net':statistics.median(r['finance']['net'] for r in allrows),'median_stock':statistics.median(r['finance']['stock'] for r in allrows),
              'our_net_rank_pooled':1+sum(r['finance']['net']>f['net'] for r in allrows),'our_stock_rank_pooled':1+sum(r['finance']['stock']>f['stock'] for r in allrows),
              'note':'Pooled rank is descriptive only; competition and market structure differ by cohort.'}
styles={}; layouts={}
for r in allrows:
    layout='both' if all(any(p['market']==m for p in r['products']) for m in ['EU','AS']) else ('EU_only' if any(p['market']=='EU' for p in r['products']) else ('AS_only' if r['products'] else 'inactive'))
    layouts.setdefault(layout,[]).append(r)
layout_stats={k:{'n':len(v),'profitable':sum(r['finance']['net']>0 for r in v),'median_net':statistics.median(r['finance']['net'] for r in v),'median_stock':statistics.median(r['finance']['stock'] for r in v)} for k,v in layouts.items()}
peer_table=[]
for r in sorted(cohort['records'],key=lambda x:x['stock_rank']):
    ff=r['finance']
    peer_table.append({'team':r['team'],'stock_rank':r['stock_rank'],'net_rank':r['net_rank'],'stock':ff['stock'],'net':ff['net'],'revenue':ff['revenue'],
        'gross_profit':ff['gross_profit'],'fixed':ff['fixed'],'rd':ff['rd'],'next_performance':ff['next_performance'],'next_battery':ff['next_battery'],
        'EU_quantity':sum(p['total_quantity'] for p in r['products'] if p['market']=='EU'),'AS_quantity':sum(p['total_quantity'] for p in r['products'] if p['market']=='AS')})
consumer=products[1]; consumer_contrib_assuming_w4=consumer['price']-consumer['unit_cost']-4
counterfactual={
 'consumer_additional_qty_for_net_zero_holding_others_fixed_warranty4':-f['net']/consumer_contrib_assuming_w4,
 'consumer_required_total_for_net_zero_holding_others_fixed_warranty4':consumer['total_quantity']-f['net']/consumer_contrib_assuming_w4,
 'double_consumer_sales_net_holding_others_fixed_warranty4':f['net']+consumer['total_quantity']*consumer_contrib_assuming_w4,
 'consumer_first_round_direct_fixed':3000+2200+900+900,
 'consumer_first_round_direct_contribution_assuming_w4':consumer['total_quantity']*consumer_contrib_assuming_w4-(3000+2200+900+900),
 'consumer_recurrent_direct_fixed_if_design_unchanged':3000+900+900,
 'consumer_recurrent_break_even_qty_assuming_w4':4800/consumer_contrib_assuming_w4,
 'net_without_rd_holding_everything_else_fixed':f['net']+f['rd'],
 'warning':'Accounting sensitivities only; no actual counterfactual demand, cannibalization, tax, repair or interest response modeled.'}
benchmark_cohort=next(c for c in practice if '棉花娃娃说得队' in c['roster'])
benchmark=next(r for r in benchmark_cohort['records'] if r['team']=='棉花娃娃说得队')
benchmark_product=next(p for p in benchmark['products'] if p['features']['camera'])
benchmark_market=benchmark_cohort['markets']['EU']
benchmark_analysis={'record':benchmark,'market':benchmark_market,
 'consumer_price':benchmark_product['price'],'consumer_qty':benchmark_product['total_quantity'],
 'consumer_segment_shares_pct':[100*q/m for q,m in zip(benchmark_product['quantity'],benchmark_market['segments'])],
 'consumer_qty_if_preserving_its_segment_shares_in_our_actual_market':sum(q/m*am for q,m,am in zip(benchmark_product['quantity'],benchmark_market['segments'],actual_market)),
 'consumer_qty_if_preserving_its_segment_shares_in_forecast_market':sum(q/m*fm for q,m,fm in zip(benchmark_product['quantity'],benchmark_market['segments'],forecast_market))}
comparison_old={k:{'practice':old['finance'][k],'formal':f[k],'difference':f[k]-old['finance'][k]} for k in ['net','revenue','gross_profit','fixed','rd','stock','forecast_error_pct']}
out={'our_result':ours,'our_market':market,'proposal_comparison':comparison,'net_bridge':bridge,'bridge_residual':sum(x['amount'] for x in bridge)-f['net'],
     'market_vs_share_decomposition':{'forecast_market_approx':forecast_market,'actual_realized_market':actual_market,'recommended_quantities':forecast,'actual_quantities':actual,
      'market_arithmetic_effect':market_volume_effect,'residual_share_arithmetic_effect':share_effect,'warning':'Arithmetic using approximate outlook, not exogenous causal attribution.'},
     'funnel':funnel,'peers':peer_table,'global_stats':global_stats,'layout_stats':layout_stats,'counterfactual_sensitivities':counterfactual,
     'benchmark_review':benchmark_analysis,'practice_comparison':comparison_old,
     'reset_evidence':{'all_current_tech_100':all(r['finance']['performance_technology']==100 and r['finance']['battery_technology']==100 for r in allrows),
                       'all_retained_zero':all(r['finance']['retained']==0 for r in allrows),'all_capital_80000':all(r['finance']['capital']==80000 for r in allrows)},
     'raw_accounting_reconciliation_errors':errors,'missing_decisions':['submitted_segment_sales_forecasts','ad_spend_by_segment','channel_spend_by_channel','rd_split','warranty_months','submitted_repair_forecasts'],
     'sources':[c['source'] for c in formal]}
out['data_quality']={'formal_files':len(formal),'practice_files':len(practice),'our_cohort_all_checks_pass':True,
 'all_income_statements_and_balance_sheets_internally_reconcile':not fatal_errors,
 'formal_cohorts_with_product_detail_warnings':sum(bool(c['reconciliation_errors']) for c in formal),
 'unresolved_cross_table_warnings':errors,
 'scope':'Financial distribution uses reconciled financial tables; anomalous foreign product cost and spend fields are not used in causal comparisons.'}
out['source_hashes']={c['source']:hashlib.sha256((ROOT/c['source']).read_bytes()).hexdigest() for c in formal+practice}
out['cash_scope_check']={'ar_product_sales_60_360_residual':f['ar']-f['product_revenue']/6,
 'ap_product_cost_10pct_residual':f['ap']-f['product_cost']*0.1,
 'prior_cash_model_error':'Previous simplified calculator applied AR/AP to repair revenue/cost too; this is inconsistent with our actual export.'}
out['units']={'financial':'thousand EUR','price_cost_stock':'EUR','volume':'thousand units'}
out['benchmark_review']['consumer_high_end_comparison']={
 'benchmark_awareness':benchmark_product['awareness'][1],'our_awareness':consumer['awareness'][1],
 'benchmark_intent_to_awareness_pct':100*benchmark_product['intent'][1]/benchmark_product['awareness'][1],
 'our_intent_to_awareness_pct':100*consumer['intent'][1]/consumer['awareness'][1],
 'benchmark_sales_to_intent_pct':100*benchmark_product['quantity'][1]/benchmark_product['intent'][1],
 'our_sales_to_intent_pct':100*consumer['quantity'][1]/consumer['intent'][1]}
out['our_summary']={'quantity_total':sum(actual),'recommended_quantity':sum(forecast),
 'quantity_shortfall_pct':100*(1-sum(actual)/sum(forecast)),
 'EU_share_pct':100*sum(actual)/market['EU']['quantity'],
 'EU_market_vs_approx_outlook_pct':100*(market['EU']['quantity']/sum(forecast_market)-1),
 'AS_market_vs_approx_outlook_pct':100*(market['AS']['quantity']/163-1),
 'all_peer_net_negative':all(r['finance']['net']<0 for r in cohort['records']),
 'previous_practice_EU_share_pct':100*sum(p['total_quantity'] for p in old['products'] if p['market']=='EU')/oldcohort['markets']['EU']['quantity'],
 'platform_estimated_net_minus_realized':f['platform_forecast_net']-f['net'],
 'market_arithmetic_shortfall':-sum(market_volume_effect),'share_arithmetic_shortfall':-sum(share_effect)}
(OUT/'diagnosis.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'all-cohorts.json').write_text(json.dumps(formal,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'peer-comparison.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    writer=csv.DictWriter(fp,fieldnames=list(peer_table[0])); writer.writeheader(); writer.writerows(peer_table)
with (OUT/'profit-bridge.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    writer=csv.DictWriter(fp,fieldnames=['item','amount']); writer.writeheader(); writer.writerows(bridge)
with (OUT/'our-product-audit.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    fields=['slot','actual_name','field','recommended','actual','same','source']
    writer=csv.DictWriter(fp,fieldnames=fields); writer.writeheader()
    for p in comparison:
        for field,v in p['checks'].items():
            writer.writerow({'slot':p['slot'],'actual_name':p['actual_name'],'field':field,**v,'source':ours['source']})
print(json.dumps({k:out[k] for k in ['global_stats','layout_stats','net_bridge','counterfactual_sensitivities','reset_evidence']},ensure_ascii=False,indent=2))
print('MARKET_BREAKDOWN',out['market_vs_share_decomposition'])
print('BENCHMARK', {k:v for k,v in benchmark_analysis.items() if k not in ['record']})
print('OUR_FULFILLMENT',[(p['slot'],sum(p['awareness']),sum(p['intent']),p['total_quantity']) for p in products])
print('LEADER',peer_table[0])

"""Transparent accounting scenarios, not a demand or stock-price prediction model."""
from pathlib import Path
import json
from decimal import Decimal as D

ROOT=Path(__file__).resolve().parents[1]
p=json.loads((ROOT/'analysis/round1_plan.json').read_text(encoding='utf-8'))
a,b=p['products']; g=p['global']; c=p['costs']; ass=p['assumptions']
fixed_parts={
 'management':c['entity_EU']+2*c['per_product_EU'],
 'production_lines':2*c['line_per_design'],
 'advertising':sum(sum(x['ads']) for x in [a,b]),
 'channels':sum(sum(x['channels']) for x in [a,b]),
 'research_reports':sum(g['market_report_cost'].values()),
 'RD':g['rd_performance']+g['rd_battery'],
 'repair_quality':g['repair_quality']}
fixed=sum(fixed_parts.values())
def evaluate(qs,uplift=0,cost_b=None,repair=False):
    rev=D(0); cost=D(0); warranty=D(0)
    for idx,(prod,q) in enumerate(zip([a,b],qs)):
        unit=prod['unit_cost_assumed'] if idx==0 or cost_b is None else cost_b
        rev+=D(str(q))*D(str(prod['price']))
        cost+=D(str(q))*D(str(unit))*(1+D(str(uplift)))
        warranty+=D(str(q))*D(str(prod['warranty_per_unit_assumed']))
    repair_cost=D(str(g['repair_quantity']['EU']))*D(str(g['repair_unit_cost_assumed']['EU'])) if repair else D(0)
    repair_rev=repair_cost*(1+D(str(g['repair_markup_pct']['EU']))/100)
    ebit=rev-cost-warranty-D(fixed)+repair_rev-repair_cost
    tax=max(D(0),ebit)*D(str(ass['tax_rate']))
    net=ebit-tax
    ar=(rev+repair_rev)*D(str(ass['payment_days']))/D(str(ass['ar_day_basis']))
    ap=(cost+repair_cost)*D(str(ass['accounts_payable_rate']))
    cash=D(str(ass['opening_net_assets']))+net+ap-ar
    return {k:float(v) for k,v in locals().copy().items() if k in ['rev','cost','warranty','repair_cost','repair_rev','ebit','tax','net','ar','ap','cash']}
out={'fixed_parts':fixed_parts,'fixed_excluding_warranty':fixed,'scenarios':{},
     'base_with_repair':evaluate(p['quantity_scenarios']['base'],repair=True),
     'base_consumer_cost_240':evaluate([65,60],cost_b=240),
     'assumptions':ass}
for name,qs in p['quantity_scenarios'].items():
    out['scenarios'][name]={str(u):evaluate(qs,u) for u in p['variable_cost_uplifts']}
contrib_a=a['price']-a['unit_cost_assumed']-a['warranty_per_unit_assumed']
contrib_b=b['price']-b['unit_cost_assumed']-b['warranty_per_unit_assumed']
out['break_even_quantity_same_mix']=fixed/((65*contrib_a+60*contrib_b)/125)
out['break_even_consumer_given_65_business']=(fixed-65*contrib_a)/contrib_b
out['segment_company_forecast']=[x+y for x,y in zip(a['quantity'],b['quantity'])]
out['segment_share_pct_approx']=[100*q/m for q,m in zip(out['segment_company_forecast'],ass['europe_market_approx'])]
out['fallback_single_fixed']=fixed-c['per_product_EU']-c['line_per_design']-sum(b['ads'])-sum(b['channels'])
out['fallback_single_ebit']=80*(449-a['unit_cost_assumed']-a['warranty_per_unit_assumed'])-out['fallback_single_fixed']
out['fallback_consumer_ebit_at_cost_cap']=65*contrib_a+55*(389-230-5)-fixed
out['reconcile_old_budget']={'EU_product_revenue':1100*400,'AS_product_revenue':165*350,
 'cash_using_displayed_rounded_values':80000+96738+33269-82958}
out['notes']=['Cash assumes reset, zero beginning liabilities and retained profits; not platform forecast.',
 'Tax illustration assumes no loss carryforward and ignores interest.',
 'Scenario uplift is a stress assumption, not an estimated penalty formula.',
 'Warranty includes provision once; fixed excludes warranty.',
 'Repair base is kept separate; scenario comparison excludes repair gross profit.']
assert fixed==20426
assert sum(out['segment_company_forecast'])==125
assert sum(a['quantity'])==65 and sum(b['quantity'])==60
assert out['scenarios']['base']['0']['rev']==54425
assert abs(out['scenarios']['base']['0']['ebit']-2491.55)<1e-6
(ROOT/'analysis/round1-scenario-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:out[k] for k in ['fixed_parts','fixed_excluding_warranty','break_even_quantity_same_mix','break_even_consumer_given_65_business','segment_share_pct_approx','fallback_single_fixed','fallback_single_ebit','fallback_consumer_ebit_at_cost_cap']},ensure_ascii=False,indent=2))
for name,values in out['scenarios'].items():
    print(name,{u:round(v['ebit'],2) for u,v in values.items()})
print('base_with_repair',out['base_with_repair'])

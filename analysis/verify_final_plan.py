from pathlib import Path
from decimal import Decimal as D
import csv, hashlib, json, re

root=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().lower()
raw=json.loads((root/'analysis/raw-inventory.json').read_text(encoding='utf-8'))
shots=json.loads((root/'data/evidence/2026-10-17/index.json').read_text(encoding='utf-8'))
archive=root/'archive/legacy-model-2026-10-17'
with (archive/'move-manifest.csv').open(encoding='utf-8-sig',newline='') as f: manifest=list(csv.DictReader(f))
assert all(sha(root/r['path'])==r['sha256'].lower() for r in raw)
assert all(sha(root/'data/evidence/2026-10-17'/r['file'])==r['sha256'].lower() for r in shots)
assert all(sha(archive/r['OriginalPath'])==r['SHA256'].lower() for r in manifest)
p=json.loads((root/'analysis/round1_plan.json').read_text(encoding='utf-8'))
r=json.loads((root/'analysis/round1-scenario-results.json').read_text(encoding='utf-8'))
assert len(p['products'])==2 and p['inactive_slots']==[3,4,5,6]
assert all(x['markets']==['EU'] for x in p['products'])
direct_revenue=D(65)*469+D(60)*399
direct_cost=D(65)*D('264.95')+D(60)*230
direct_warranty=D(65)*D('3.78')+D(60)*4
direct_fixed=D(7000+4400+1900+1900+1200+4000+26)
direct_profit=direct_revenue-direct_cost-direct_warranty-direct_fixed
assert float(direct_profit)==r['scenarios']['base']['0']['ebit']
assert direct_revenue==54425 and direct_profit==D('2491.55')
assert p['fallback_consumer']['quantity']==[8,33,3,11]
assert sum(p['fallback_single']['quantity'])==80
for file in ['current/final-round1-plan.md','current/round1-entry-checklist.md']:
    path=root/file
    s=path.read_text(encoding='utf-8')
    for link in re.findall(r'\]\((<[^>]+>|[^)]+)\)',s):
        target=link.strip('<>')
        if '://' not in target: assert (path.parent/target).exists(),target
summary={'version':p['version'],'raw_files_verified':len(raw),'screenshots_verified':len(shots),
         'archived_files_verified':len(manifest),'base_revenue_recomputed':float(direct_revenue),
         'base_product_ebit_recomputed':float(direct_profit),'local_document_links':'verified',
         'platform_quote_for_new_product':'not_verified','actual_demand':'unknown','submission':'not_performed',
         'outputs':{name:sha(root/name) for name in ['current/final-round1-plan.md','current/round1-entry-checklist.md','analysis/round1_plan.json','analysis/round1-scenario-results.json']}}
(root/'analysis/final-validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))

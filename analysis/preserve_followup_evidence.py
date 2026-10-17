from pathlib import Path
import hashlib
import json
import shutil

root = Path(__file__).resolve().parents[1]
dest = root / 'data/evidence/2026-10-17'
items = [
('8e06ba27-3ee5-4e6d-941e-14d067294f54','14-schedule'),
('2deeb9a2-232f-42ed-8e1c-3df227513b03','15-outlook-europe'),
('9452e449-714e-4382-a1b1-017feabd11e0','16-outlook-asia'),
('8a423b8d-c9cd-44f9-8e2b-e7e947a6f9b2','17-checklist-overview'),
('3dbaa35d-461f-401e-ab26-0880864b4f56','18-checklist-europe-channels'),
('65528409-2277-40f9-b84b-6f9300e353ae','19-checklist-empty-slots'),
('249bacaa-029f-47cb-9e6c-6b7df137a753','20-checklist-empty-slots'),
('e2b4638b-9fb7-45e1-a326-3793065e8637','21-checklist-empty-slots'),
('5ee830c2-9417-4e74-bdad-0269c4db4981','22-checklist-asia-product2'),
('52367a1e-535b-48cd-ba1a-dd8b0f32de02','23-checklist-design'),
('5a12f22f-5d9a-495d-bb5c-9dbae0a1052d','24-checklist-design-empty'),
('1bf85b0b-fccd-4e61-abd4-c13f5e983c3e','25-checklist-service-finance'),
]
index_path = dest / 'index.json'
index = json.loads(index_path.read_text(encoding='utf-8'))
for ident, name in items:
    src = Path('C:/Users/grass/AppData/Local/Temp') / f'codex-clipboard-{ident}.png'
    target = dest / (name + '.png')
    shutil.copy2(src, target)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    assert digest == hashlib.sha256(target.read_bytes()).hexdigest()
    index = [entry for entry in index if entry['id'] != name[:2]]
    index.append({'id':name[:2], 'file':target.name, 'source':src.name, 'sha256':digest,
                  'provenance':'用户后续补充截图；日程页显示2026-10-17 20:46，其余逐图拍摄时间未核实'})
index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
print('Verified and indexed',len(items),'new screenshots; total',len(index))

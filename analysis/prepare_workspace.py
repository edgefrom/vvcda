"""Preserve supplied evidence and install the reviewed workspace entry points."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / 'current/final-round1-plan.md').exists():
    raise SystemExit('Historical preparation script: refusing to overwrite newer final-decision entry points.')
docs = {
 'AGENTS.md': '''# 当前协作规则

本仓库用于 CESIM Marketing 手机案例，目标是期末赛区股价第一。旧模型曾用于表现不佳的练习回合，不能作为已验证规则或决策依据。

## 阅读入口和证据优先级
1. 先读根目录 README.md 和 current/review-before-decision.md，确认工作边界。
2. 原始依据是 data/raw 中的指南、调研和比赛结果，以及 data/evidence 中用户提供的截图。截图是页面快照，不保证网站现值未变。
3. current 是本次重新核对后的工作材料，仍须区分事实、推论和未确认事项。与原始证据冲突时修正工作材料。
4. archive/legacy-model-2026-10-17 只供追溯。其代码、配置、拟合、策略、README 和旧代理指南均不具备当前权威性，不自动运行或沿用。

## 当前授权边界
用户要求自动推进到给出完整决策方案之前，再交其审查。允许整理、读取、核对、诊断和准备候选方向；尚未授权确定完整最终录入值、修改网站决策、覆盖小组方案或提交。

## 数据与技术
- 保留原始文件，不覆盖比赛结果；推导结果写入 analysis。
- 注意千欧元与欧元、千台与台。预算销量不等于实际需求。
- 回合、赛区和队伍共同识别样本；第二次练习存在重复导出，先去重。
- 如需 Python，使用系统环境，不创建 venv。
- 旧技术约定见归档 original-AGENTS.md，仅在明确修复旧模型时参考。
- 决策记录必须保留来源、假设和人类审查意见。
''',
 'README.md': '''# CESIM 决策审查工作区

当前阶段：**事实核对及候选方向审查；尚未形成最终决策录入表，也未修改网站决策。**

请先阅读 [决策前审查材料](current/review-before-decision.md)，再看 [事实与数据口径](current/facts.md) 和 [规则核对](current/rules-verified.md)。

| 位置 | 用途 | 可靠性说明 |
|---|---|---|
| data/raw | 原始指南、调研、两次练习结果 | 优先证据；核对回合、单位和重复导出 |
| data/evidence/2026-10-17 | 用户网站截图及索引 | 页面快照；预算不是实际结果 |
| current | 本次审查材料 | 区分事实、推论和待确认事项 |
| analysis | 本次独立读取脚本与中间数据 | 诊断工具，尚不能预测对手 |
| archive | 旧代码、配置、文档和策略 | **未验证历史参考，不可自动沿用** |
| tmp | PDF 渲染等临时文件 | 非正式决策材料 |

旧目录整体移动，不删除原文件。归档 move-manifest.csv 记录原路径及 SHA256；113 个移动文件内容已核对一致。原始比赛资料保留原处，已有 Git 改动没有回滚。

截止安排按用户指定的今晚 22:00。后续录入阶段须再次核验网站回合、截止时间和小组实际生效方案。
''',
 'archive/README.md': '''# 历史参考隔离区

**这里的材料不完全可靠，不能视为比赛规则、当前状态或已验证最优策略。**

legacy-model-2026-10-17 保留旧代码、配置、测试、脚本和文档。测试通过只能说明部分实现符合自身假设，不能证明假设符合 CESIM。即使旧文档使用“真实”“验证”“最优”等字样，也需重新核对来源。

原文件不改写，便于追溯；其中 README 和 original-AGENTS.md 仅说明历史项目。当前入口是根目录 README.md 和 AGENTS.md。

已发现风险包括：亚洲外观偏好配置与原调研不符；需求与预算口径混淆；特征标记读取、竞争需求和财务模拟存在问题；旧策略不能直接代表正式第一回合。

移动清单见 legacy-model-2026-10-17/move-manifest.csv。数据原件保留在 data/raw，因为原始证据仍需使用。
'''
}
for rel, content in docs.items():
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')

shots = [
 ('f5e414b2-1fd6-4cdb-b876-e995a2a97f01','01-asia-market-outlook'),
 ('41a23906-64aa-48b2-95b3-db29c9ae2cdf','02-product-design'),
 ('9b2a1d09-aa6c-4084-b6d9-c040eee57dce','03-research-development'),
 ('cfcccd8e-cbec-416f-90fb-de4770bfcc29','04-budget-income-top'),
 ('be0814a4-32ad-4e62-bc88-91006b5419a2','05-decision-areas'),
 ('81fe0517-72ba-4116-976b-15604063b5d4','06-europe-price'),
 ('29e9cf62-244a-4760-87ea-72d7797268a4','07-asia-price'),
 ('308387ba-c418-4e8d-8da9-b91740433a5e','08-warranty'),
 ('8b97de01-7245-4a38-b4d2-f88caded074b','09-round-parameters'),
 ('c3784aa7-fbb4-44a0-b8bb-0acd0261eecf','10-budget-balance-sheet'),
 ('b335ca7f-3c1f-4da3-8679-cf0f5b7b9133','11-budget-income-full'),
 ('16379447-c064-44cb-92a4-841a9294e7fe','12-europe-marketing'),
 ('590eead3-9719-45a6-9088-48256cd75a9c','13-asia-marketing'),
]
dest = ROOT / 'data/evidence/2026-10-17'
dest.mkdir(parents=True, exist_ok=True)
index = []
for ident, name in shots:
    src = Path('C:/Users/grass/AppData/Local/Temp') / f'codex-clipboard-{ident}.png'
    target = dest / (name + '.png')
    shutil.copy2(src, target)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    assert digest == hashlib.sha256(target.read_bytes()).hexdigest()
    index.append({'id':name[:2], 'file':target.name, 'source':src.name, 'sha256':digest,
                  'provenance':'用户在本对话提供；快照时间未单独核实，不是实时网站读取'})
(dest / 'index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
raw_index = [{'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in sorted((ROOT/'data/raw').rglob('*')) if p.is_file()]
(ROOT/'analysis/raw-inventory.json').write_text(json.dumps(raw_index, ensure_ascii=False, indent=2), encoding='utf-8')
audit = (ROOT/'tmp/inspect_practice.py').read_text(encoding='utf-8')
audit = audit.replace("Path('tmp/practice_summary.json')", "Path('analysis/practice_summary.json')")
(ROOT/'analysis/inspect_practice.py').write_text(audit, encoding='utf-8')
shutil.copy2(ROOT/'tmp/practice_summary.json', ROOT/'analysis/practice_summary.json')
print(f'Created entry points; preserved {len(index)} screenshots; inventoried {len(raw_index)} raw files.')

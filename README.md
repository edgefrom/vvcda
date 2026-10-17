# CESIM 决策审查工作区

团队共享仓库：https://github.com/edgefrom/vvcda 。**新电脑／新GPT先读[接手说明](docs/HANDOFF.md)和[协作开发规范](docs/DEVELOPMENT.md)，再读当前诊断。** 原始数据、截图、分析结果和历史归档均随库传递，聊天背景不会自动随文件传递。

快速校验：Python3.11+系统环境，`python -m pip install -r requirements.txt`，然后 `python -X utf8 analysis/verify_workspace.py`。只阅读资料无需安装；当前工具不依赖旧模型。

当前阶段：**正式第一轮已结算，已完成原始结果诊断及首轮方案复盘。当前尚无第二轮完整建议。**

当前入口：[第一轮完整诊断](current/formal-round1-diagnosis.md)。本队净利润-5124.64千欧元、股价4.3187欧元，同赛区分别第2／10、第4／10。消费者款外观与建议不同，其他若干最终提交分项仍无法从结果直接反查。不能将原建议自动当作实际提交。

证据入口：[本队正式结果](data/raw/formal/round-01/cohort-4d75bca778b9-08e2a398.xls)、[诊断底稿与完整勾稽](analysis/formal-round-01/diagnosis.json)、[人工入件规范](current/data-intake-policy.md)、[本次入件来源清单](data/intake/20261017T221830.json)。

历史追溯：[事前完整建议](current/final-round1-plan.md)、[事前录入清单](current/round1-entry-checklist.md)、[冻结快照及哈希](archive/decision-snapshots/formal-round-01/manifest.json)。这些文件与 analysis/round1_plan.json、round1-scenario-results.json 均保留原预测，**不是实际结果或下一轮输入**。原简化现金计算有口径错误，修正见最新诊断。

current/facts.md、readiness-check.md、review-before-decision.md 是首轮决策前阶段材料；25张网站截图是当时快照，其中预算不是实际业绩。规则背景见 current/rules-verified.md，仍以原始指南／调研为准。正式结果现支持财务和技术重置，隐含品牌、渠道状态仍未完全确认。

| 位置 | 用途 | 可靠性说明 |
|---|---|---|
| manual | 人工下载收件箱 | 每次阅读顺手整理；README 留存，其余原件归档 |
| data/raw | 原始指南、调研、练习及正式结果 | 优先证据；核对回合、单位、重复及源数据异常 |
| data/intake | 入件来源映射、哈希和分类记录 | 能追溯原下载路径及去重依据 |
| data/evidence/2026-10-17 | 用户网站截图及索引 | 页面快照；预算不是实际结果 |
| current | 本次审查材料 | 区分事实、推论和待确认事项 |
| analysis | 本次独立读取脚本与中间数据 | 诊断工具，尚不能预测对手 |
| archive/legacy-model-2026-10-17 | 旧模型、配置、拟合及策略 | **未验证历史参考，不可自动沿用** |
| archive/manual-imports | 完整人工下载原件 | 来源存档；按入件清单定位规范副本 |
| archive/decision-snapshots | 事前方案及预测冻结快照 | 复盘依据，不得修改来贴合实际结果 |
| tmp | PDF 渲染等临时文件 | 非正式决策材料 |

旧目录整体移动，不删除原文件。归档 move-manifest.csv 记录原路径及 SHA256；113 个移动文件内容已核对一致。原始比赛资料保留原处，已有 Git 改动没有回滚。

第一轮截止时间为2026-10-17 22:00，已结束。后续决策必须重新核对回合、截止时间、当前参数及小组生效版本。本代理本次没有修改网站或提交决策。

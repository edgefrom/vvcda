# 分析材料索引与使用边界

当前正式第一轮复盘入口：`formal-round-01/diagnosis.json`，配套原始逐队数据、对照CSV和验证记录位于同一目录。可读报告为 `../current/formal-round1-diagnosis.md`。

当前读取工具：

- `verify_workspace.py`：新电脑接手时只读核验原件、截图、旧归档、冻结方案和正式结果，不写回业务文件。

- `ingest_manual.py`：manual 人工资料预检／归档。默认不移动，`--apply` 才执行；遵守 `../current/data-intake-policy.md`。
- `results_reader.py`：校验当前290行结果导出格式、显式保留特性，并检查报表等式。布局不符停止；明细不一致记录异常，不自动补数。
- `diagnose_formal_round1.py`：从正式原件和事前方案重新计算本轮对账、同赛区对照与有限描述统计，不调用旧需求模型。
- `write_formal_round1_report.py`：生成本轮可读报告和图表。

`round1_plan.json`、`round1-scenario-results.json`、`calculate_round1_scenarios.py`、`final-validation.json` 等为**事前建议或历史计算**，不是实际提交／实际结果。原情景并非需求预测；旧现金计算把维修纳入应收／应付，已被实际结果纠正。为避免覆盖审计记录，不应重新运行旧方案生成器来更新同名历史文件。

已冻结上述主要历史输入与计算，见 `../archive/decision-snapshots/formal-round-01/manifest.json`。后续回合应另建目录和版本，不复用首轮假设冒充新证据。

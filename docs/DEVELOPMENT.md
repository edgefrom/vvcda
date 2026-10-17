# 协作与开发规范

## 版本和协作

本仓库用于交换所有项目资料。原始数据、截图、压缩包、报告、图表、派生结果和归档全部纳入；只忽略缓存、编译产物、编辑锁文件及机器凭据。不忽略data、analysis、manual或archive。

开始任务检查git status，再fetch核对远程。干净工作区可git pull --ff-only；有修改先保存自己的提交／分支，不用reset --hard覆盖。并行成员分别使用codex/round2-demand、codex/stock-audit等分支，提交并推送后由负责人整合。main保存已整合成果，禁止强推团队历史。冲突先读两边证据，不能机械选择一侧。

交接注明起始／最终提交、改动、依据、验证及缺口。比赛录入清单只有一个明确批准版本，录入后保存小组回读和微调记录。对话不是持久协作记录，关键结论须落盘。

根目录已不再是旧src/cda可安装包。旧代码、配置、测试及pyproject整体归档；不要自动恢复或按旧AGENTS重建它。修复旧模型须有明确任务及新验证。

## 证据规范

- 原件不可变，哈希连接来源及规范副本；不同回合／赛区／版本不覆盖。
- 财务千欧元、销量千台、价格／成本／股价欧元；空白、0、x分别处理。
- AI建议、实际提交、平台预算、实际结果分别标识；缺失字段不得反猜成已确认。
- 冻结方案不可改。报告更新通过版本／Git保留旧结论，不事后更改预测。
- 记录清洗、重复、异常、排除规则和源哈希，不只选择成功案例。
- 会计正确不证明需求预测正确；相关性不等于因果；跨赛区模型按赛区留出验证，不自造精确股价公式称官方规则。
- 文档使用相对链接，脚本从自身位置定位根目录；不要硬编码本机目录。历史Windows路径保留作来源，读取时兼容转换。
- .gitattributes禁用自动换行转换，保持原件／快照SHA256跨平台一致，不批量格式化历史JSON、CSV、Markdown。

## 当前工具

Python3.11+，系统环境，不建venv；安装根requirements.txt。

```text
python -X utf8 analysis/verify_workspace.py
python -X utf8 analysis/ingest_manual.py
python -X utf8 analysis/ingest_manual.py --apply
python -X utf8 analysis/diagnose_formal_round1.py
python -X utf8 analysis/write_formal_round1_report.py
```

verify只读检查原件、快照及勾稽。ingest默认预检，--apply才归档，执行前审阅分类。diagnose重建首轮派生结果，write重建报告和图表；运行后审查差异。后续回合另建目录，不将首轮工具当通用预测器。

prepare_workspace、preserve_followup_evidence、build_entry_checklist、calculate_round1_scenarios等是历史流程，可能使用旧路径或覆盖历史文件，不是新电脑初始化命令。

解析器改动须核验标签、分群／渠道／漏斗销量、产品收入／成本、营销汇总、利润表和资产负债表，用真实已知及异常案例验证。改输出字段同步docs/technical/data-contracts.md。旧模型测试不证明平台规则正确。

## 网络和发布

仓库提供GitHub Actions，在Windows和Linux、Python3.11上运行同一份证据校验。检查通过只表示来源与会计一致，不证明预测模型有效。首次推送后的云端结果应查看Actions；本机通过不能冒称云端已通过。

仅同步用户指定仓库，不擅自改变仓库可见性。令牌、密码及网站会话不写入文档。同步结束核对远程提交，不把本地提交误报成已推送。

用户允许遇到网络问题尝试本地7897代理；优先临时配置，不修改所有成员的全局设置：

```text
git -c http.proxy=http://127.0.0.1:7897 fetch origin
git -c http.proxy=http://127.0.0.1:7897 push origin HEAD
```

另一台电脑需确认该端口确实提供代理。缺少网络／认证时明确说明阻碍，不声称已同步。

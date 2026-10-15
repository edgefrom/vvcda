# 商海之弈 · 决策支持工具（CDA）

回合制商业模拟（CESIM Marketing 平台 · 手机案例）的经营决策支持系统。
目标：让本队在 10 回合结束时**赛区期末股价第 1**（仅第 1 名晋级）。
---

## 快速开始

```powershell
# 安装依赖（系统 Python，无 venv）
python -m pip install -r requirements.txt

# 运行测试
python -m pytest

# 核心算法端到端演示（合成数据 → 需求估计 → 蒙特卡洛 → 搜索 → 建议）
python scripts/demo.py
```

## 目录结构

```
cda/
├── IMPORTANT.md            # ⭐ 入口：当前回合决策卡（最优先看这个）
├── AGENTS.md               # AI 代理 / 协作者指南
├── config/                 # 平台相关配置（登录后按真实平台填写）
│   ├── decision_schema.yaml   # 决策表单字段定义
│   └── market_research.yaml   # 市场调研转写（8 细分×偏好，先验来源）
├── data/
│   └── raw/                # 原始下载物（入库）
│       ├── 决策指南.pdf / 市场调研报告.pdf
│       └── results/        # 练习回合结果 xls（23 份）
├── src/cda/                # 平台无关核心算法包
│   ├── schemas.py          # 统一数据结构（全项目依赖根）
│   ├── adapters/           # 数据适配层（JSON/CSV/内存 + 注册表 + xls 解析）
│   ├── demand/             # 需求模型（logit 基线 + 贝叶斯 + RLS）
│   ├── opponent/           # 对手建模（类型识别 + 纳什预判）
│   ├── optimize/           # 约束 + 差分进化 / 分层搜索
│   ├── eval/               # 财务仿真 + 蒙特卡洛 + 代理目标
│   └── output/             # 建议格式化（Markdown）
├── scripts/                # 命令行入口（demo.py 端到端演示）
├── tests/                  # 合成数据测试
└── docs/
    ├── guides/             # 给全队看（算法解读/工作流/复盘/提取）
    ├── technical/          # 给技术看（架构/数据契约/建模决策）
    └── decision-log/       # 每回合决策日志
```

## 文档导航

| 文档 | 内容 | 读者 |
|---|---|---|
| `IMPORTANT.md` | ⭐ **入口**：当前回合决策卡（截止时间/照抄值/交卷清单） | 👥 全队 |
| `docs/guides/algorithm-explained.md` | 算法通俗解读（做什么、能/不能帮你什么） | 👥 全队 |
| `docs/guides/workflow.md` | 每日闭环工作流 + 练习回合实验设计 | 👥 全队 |
| `docs/guides/round1-analysis.md` | 练习回合 1 全市场复盘（弹性/盈利密码） | 👥 全队 |
| `docs/guides/decision-guide-extracted.md` | 决策指南 36 页的规则与决策空间提取 | 👥 全队 |
| `docs/guides/market-research-extracted.md` | 市场调研报告 9 页的结构化提取 | 👥 全队 |
| `docs/technical/architecture.md` | 分层架构与模块边界 | 技术 |
| `docs/technical/data-contracts.md` | 统一数据结构与配置字段的精确含义 | 技术 |
| `docs/technical/modeling-decisions.md` | 建模决策记录（方法论、优先级、砍掉/保留项） | 技术 |
| `docs/decision-log/template.md` | 每回合决策日志模板 | 👥 全队 |
| `AGENTS.md` | 面向 AI 代理的仓库指南（约定、命令、红线） | AI |

## 设计原则

1. **平台相关与算法核心分离**：真实平台的字段名只出现在 `config/*.yaml` 和适配层，
   核心结构不随平台变化；未来换平台（决赛 Global Challenge）只改配置与适配器。
2. **小样本在线学习**：需求模型是「结构化先验 + 每回合在线更新」，不依赖大量训练数据。
3. **人类在环**：所有建议输出都带依据、置信度、备选方案与风险，供人类审核。

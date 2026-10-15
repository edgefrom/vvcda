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

# 启动决策支持界面
python -m streamlit run ui/app.py
```

## 目录结构

```
cda/
├── config/                 # 平台相关的配置（登录后按真实平台填写）
│   ├── decision_schema.yaml   # 决策表单字段定义（ground truth）
│   └── market_research.yaml   # 市场调研文件转写（8 细分×偏好，先验来源）
├── data/                   # 每回合数据（不入库，见 .gitignore）
│   ├── turns/              # 每回合完整记录（JSON）
│   ├── experiments/        # 受控实验记录
│   └── opponents/          # 对手档案
├── src/cda/                # 平台无关的核心包
│   ├── schemas.py          # 统一数据结构（全项目依赖根）
│   ├── adapters/           # 多接口数据适配层（JSON/CSV/内存 + 注册表）
│   ├── demand/             # 需求模型（logit 吸引力基线，可在线更新）
│   ├── opponent/           # 对手建模（类型识别）
│   ├── optimize/           # 约束 + 差分进化搜索
│   ├── eval/               # 蒙特卡洛情景评估 + 代理目标
│   └── output/             # 建议格式化（人类可读）
├── ui/app.py               # Streamlit 界面（录入/存档/建议）
├── tests/                  # 合成数据测试
└── docs/                   # 架构、数据契约、工作流、决策日志模板
```

## 文档导航

| 文档 | 内容 | 读者 |
|---|---|---|
| `docs/algorithm-explained.md` | **算法通俗解读**（这套系统在做什么、能/不能帮你什么） | 👥 全队 |
| `docs/modeling-decisions.md` | 建模决策记录（方法论、优先级、砍掉/保留项） | 技术 |
| `docs/architecture.md` | 分层架构与模块边界 | 技术 |
| `docs/data-contracts.md` | 统一数据结构与配置字段的精确含义 | 技术 |
| `docs/market-research-extracted.md` | 市场调研报告 9 页的结构化提取 | 全队 |
| `docs/decision-guide-extracted.md` | 决策指南 36 页的规则与决策空间提取 | 全队 |
| `docs/workflow.md` | 每日闭环工作流 + 练习回合实验设计 | 全队 |
| `docs/decision-log/template.md` | 每回合决策日志模板 | 全队 |
| `AGENTS.md` | 面向 AI 代理的仓库指南（约定、命令、红线） | AI |

## 设计原则

1. **平台相关与算法核心分离**：真实平台的字段名只出现在 `config/*.yaml` 和适配层，
   核心结构不随平台变化；未来换平台（决赛 Global Challenge）只改配置与适配器。
2. **小样本在线学习**：需求模型是「结构化先验 + 每回合在线更新」，不依赖大量训练数据。
3. **人类在环**：所有建议输出都带依据、置信度、备选方案与风险，供人类审核。

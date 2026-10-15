# AGENTS.md — 仓库指南（给 AI 代理 / 协作工具）

本文件帮助任何 AI 代理快速理解本仓库并正确协作。

## 项目是什么

商海之弈（CESIM Marketing 手机案例）回合制经营决策支持系统。目标：期末赛区股价第 1。
本质是「参数未知 + 9 个自适应对手」的序贯决策问题，不是有标准答案的题。

## 技术约定

- Python 3.11+，系统环境（**不创建 venv**）。
- 依赖：numpy、pandas、scipy、pydantic>=2、PyYAML、pytest（见 `pyproject.toml`）。
- 核心包 `src/cda`，**平台无关**；平台相关逻辑只在 `config/*.yaml` 与 `src/cda/adapters/`。
- 数据结构定义在 `src/cda/schemas.py`（全项目依赖根），改结构先改这里。

## 常用命令

```powershell
python -m pytest                          # 跑全部测试
python -m pytest tests/test_demand_recover.py -v   # 单测
python scripts/demo.py                    # 核心算法端到端演示
```

## 新增数据源的步骤

1. 在 `src/cda/adapters/` 新建类，继承 `DataSource`（`src/cda/adapters/base.py`）。
2. 在 `src/cda/adapters/registry.py` 注册一个名字。
3. 在 `tests/test_adapters.py` 增加往返读写测试。

## 新增需求模型 / 优化器的步骤

1. 实现 `src/cda/demand/base.py` 中的 `DemandModel` / `DemandEstimator` 接口。
2. 或实现 `src/cda/optimize/search.py` 中的搜索函数签名。
3. 用合成数据写恢复/收敛测试（见 `tests/`）。

## 文档维护原则

- 每次改动接口或配置字段，同步更新 `docs/technical/data-contracts.md`。
- 每回合决策记录走 `docs/decision-log/template.md`，保留人类决策理由。

"""Streamlit 决策支持界面：数据录入 / 结果存档 / 建议查看。

运行：python -m streamlit run ui/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st  # noqa: E402

from cda.adapters import JsonDataSource  # noqa: E402
from cda.config import load_decision_schema, load_market_research  # noqa: E402
from cda.demand import LogitDemandEstimator  # noqa: E402
from cda.eval import EvaluationResult, FinancialModel, ProxyObjective, evaluate_decision, make_scenarios  # noqa: E402
from cda.optimize import differential_evolution_search  # noqa: E402
from cda.output import Alternative, Recommendation  # noqa: E402
from cda.schemas import DecisionVector, Financials, SegmentOutcome, TurnRecord  # noqa: E402

DATA_DIR = ROOT / "data" / "turns"
SCHEMA_PATH = ROOT / "config" / "decision_schema.yaml"
RESEARCH_PATH = ROOT / "config" / "market_research.yaml"

st.set_page_config(page_title="商海之弈 · 决策支持", layout="wide")
st.title("商海之弈 · 决策支持工具")
st.caption("决策支持工具，仅供团队讨论参考；最终决策由团队理解、讨论并人工提交。")


@st.cache_data(show_spinner=False)
def _load_schema():
    if SCHEMA_PATH.exists():
        return load_decision_schema(str(SCHEMA_PATH))
    return None


@st.cache_data(show_spinner=False)
def _load_research():
    if RESEARCH_PATH.exists():
        return load_market_research(str(RESEARCH_PATH))
    return None


schema = _load_schema()
research = _load_research()
source = JsonDataSource(directory=str(DATA_DIR))

tab_entry, tab_archive, tab_advice = st.tabs(["① 数据录入", "② 结果存档", "③ 建议查看"])


# ---------------- ① 数据录入 ----------------
with tab_entry:
    st.header("回合数据录入")
    if schema is None:
        st.warning("未找到 config/decision_schema.yaml，请先完成表单 schema 抄录。")
    else:
        with st.form("entry_form"):
            turn = st.number_input("回合号", min_value=1, value=1, step=1)
            col1, col2 = st.columns(2)
            values: dict[str, float] = {}
            fields = list(schema.fields.values())
            half = len(fields) // 2 + len(fields) % 2
            for i, f in enumerate(fields):
                target = col1 if i < half else col2
                default = f.default if f.default is not None else 0.0
                if f.kind == "integer":
                    values[f.name] = float(target.number_input(f.name, value=int(default), step=1))
                else:
                    values[f.name] = float(target.number_input(f.name, value=default))

            st.markdown("**细分结果**（our_sales 与 market_sales；份额自动计算）")
            outcome_inputs: list[dict] = []
            for m in schema.markets:
                st.markdown(f"#### 市场 {m}")
                cols = st.columns(2)
                for idx, s in enumerate(schema.segments):
                    c = cols[idx % 2]
                    with c:
                        c.markdown(f"**{s}**")
                        our_sales = c.number_input(f"{m}.{s} 我方销量", value=0.0, key=f"os_{m}_{s}")
                        market_sales = c.number_input(f"{m}.{s} 市场总销量", value=0.0, key=f"ms_{m}_{s}")
                        outcome_inputs.append({"m": m, "s": s, "os": our_sales, "ms": market_sales})

            st.markdown("**财务结果**")
            fc = st.columns(5)
            revenue = fc[0].number_input("revenue", value=0.0)
            cost = fc[1].number_input("cost", value=0.0)
            profit = fc[2].number_input("profit", value=0.0)
            cash = fc[3].number_input("cash", value=0.0)
            inventory = fc[4].number_input("inventory", value=0.0)
            stock_price = st.number_input("stock_price", value=0.0)
            notes = st.text_input("决策备注（人类理由）", value="")

            submitted = st.form_submit_button("保存本回合记录")

        if submitted:
            outcomes: list[SegmentOutcome] = []
            for item in outcome_inputs:
                share = item["os"] / item["ms"] if item["ms"] > 0 else 0.0
                outcomes.append(
                    SegmentOutcome(market=item["m"], segment=item["s"], our_sales=item["os"], market_sales=item["ms"], our_share=share)
                )
            record = TurnRecord(
                turn=int(turn),
                decision=DecisionVector(turn=int(turn), values=values, notes=notes),
                outcomes=outcomes,
                financials=Financials(revenue=revenue, cost=cost, profit=profit, cash=cash, inventory=inventory),
                stock_price=stock_price if stock_price else None,
            )
            source.save_turn(record)
            st.success(f"已保存第 {turn} 回合记录到 data/turns/")


# ---------------- ② 结果存档 ----------------
with tab_archive:
    st.header("历史回合存档")
    turns = source.load_turns()
    if not turns:
        st.info("暂无记录。请先在「数据录入」页保存回合数据。")
    else:
        rows = []
        for r in turns:
            row = {"turn": r.turn, "stock_price": r.stock_price, "notes": r.decision.notes}
            row.update(r.decision.values)
            if r.financials is not None:
                row.update({"revenue": r.financials.revenue, "cost": r.financials.cost, "profit": r.financials.profit, "cash": r.financials.cash})
            rows.append(row)
        st.dataframe(rows, use_container_width=True)
        st.subheader("最近一条完整记录（JSON）")
        import json

        from cda.adapters.serialize import turn_to_dict

        st.json(turn_to_dict(turns[-1]))


# ---------------- ③ 建议查看 ----------------
with tab_advice:
    st.header("方案建议")
    if schema is None:
        st.warning("缺少决策表单 schema，无法生成建议。")
    else:
        turns = source.load_turns()
        usable = [r for r in turns if any(0.0 < o.our_share < 1.0 for o in r.outcomes)]
        if len(usable) < 2:
            st.info(
                f"可用观测不足（当前 {len(usable)} 条，需 ≥2 条且份额落在 (0,1)）。\n\n"
                "请先按练习回合受控实验设计录入数据：每回合只变少数变量，记录完整「决策→结果」。"
            )
        else:
            try:
                features = [f for f in schema.continuous_fields() if f != "production_qty"]
                estimator = LogitDemandEstimator(features)
                model = estimator.fit(usable)
            except ValueError as exc:
                st.error(f"需求估计失败：{exc}")
                st.stop()

            st.subheader("已估计需求弹性")
            st.write({k: round(v, 4) for k, v in model.feature_betas.items()})

            markets_segments = [(m, s) for m in schema.markets for s in schema.segments]
            # 市场规模优先取市场调研文件的 size；未填写时回退 1.0（注意与成本同尺度）
            market_sizes: dict[tuple[str, str], float] = {}
            for (m, s) in markets_segments:
                pref = research.get(m, s) if research is not None else None
                size = pref.size if pref is not None and pref.size > 0 else 1.0
                market_sizes[(m, s)] = size
            scenarios = make_scenarios(model, markets_segments, noise_std=0.1, n_scenarios=200, market_sizes=market_sizes)
            fin_model = FinancialModel()
            objective = ProxyObjective()

            bounds = schema.bounds()
            integer_fields = tuple(schema.integer_fields())

            def objective_fn(d: dict[str, float]) -> float:
                decision = DecisionVector(turn=0, values=d)
                res = evaluate_decision(decision, scenarios, fin_model, objective)
                return -res.mean  # 最大化代理目标

            if st.button("运行优化搜索"):
                with st.spinner("搜索中…"):
                    result = differential_evolution_search(objective_fn, bounds, integer_fields=integer_fields, maxiter=200)
                best = DecisionVector(turn=0, values=result.best)
                eval_res: EvaluationResult = evaluate_decision(best, scenarios, fin_model, objective)
                rec = Recommendation(
                    turn=(turns[-1].turn + 1) if turns else 1,
                    decision=best,
                    rationale="在估计需求模型 + 蒙特卡洛情景下最大化代理目标（利润/份额/增长加权）。",
                    confidence="low",
                    alternatives=[Alternative(decision=best, rationale="基准建议（数据不足，仅供讨论）")],
                    risks=[
                        "需求参数仅由少量回合估计，不确定性高；",
                        "股价函数为黑箱，当前目标是代理目标；",
                        "对手行为未纳入本版优化（防守层面请人工判断）。",
                    ],
                )
                st.markdown(rec.to_markdown())
                st.caption(f"情景评估：{eval_res.summary()}")

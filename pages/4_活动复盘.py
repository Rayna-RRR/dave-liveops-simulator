import pandas as pd
import streamlit as st

from src.data_loader import load_ab_test_results_data
from src.display_labels import (
    AB_METRIC_LABELS,
    EVENT_ORDER,
    SEGMENT_ORDER,
    get_event_label,
    get_segment_label,
)
from src.insight_generator import generate_postmortem_insights, infer_primary_goal, select_best_variant
from src.ui import (
    block_spacer,
    clear_interaction_state,
    ensure_interaction_value,
    filter_card,
    init_page,
    metric_to_review_focus,
    render_analysis_flow,
    render_compact_list,
    render_context_bar,
    render_empty_state,
    render_page_header,
    render_status_note,
    render_status_row,
    section_card,
    set_interaction_state,
    sync_widget_state,
)

KPI_LABELS = {
    **AB_METRIC_LABELS,
    "reward_cost": "奖励成本",
    "inflation_risk": "通胀风险",
}
VARIANT_LABELS = {"A": "方案A", "B": "方案B"}
REVIEW_FOCUS_OPTIONS = ["综合表现", "活跃", "留存", "付费", "成本"]
REVIEW_FOCUS_METRICS = {
    "综合表现": [
        "participation_rate",
        "dau_uplift",
        "d7_retention_uplift",
        "payment_conversion_uplift",
    ],
    "活跃": ["participation_rate", "dau_uplift"],
    "留存": ["d1_retention_uplift", "d7_retention_uplift"],
    "付费": ["payment_conversion_uplift", "arppu_uplift"],
    "成本": ["reward_cost", "inflation_risk"],
}
FOCUS_DEFAULT_METRIC = {
    "综合表现": "dau_uplift",
    "活跃": "dau_uplift",
    "留存": "d7_retention_uplift",
    "付费": "payment_conversion_uplift",
    "成本": "inflation_risk",
}


init_page("活动复盘")


@st.cache_data
def load_ab_test_results():
    """Load synthetic A/B results for postmortem analysis."""
    return load_ab_test_results_data()


def format_value(metric_key, value):
    """Format KPI values according to their metric type."""
    if metric_key == "reward_cost":
        return f"¥{value:.2f}"
    return f"{value:.1%}"


def format_delta(metric_key, delta_value):
    """Format metric deltas for the review metric cards."""
    if metric_key == "reward_cost":
        return f"¥{delta_value:+.2f}"
    return f"{delta_value:+.1%}"


def infer_review_focus(raw_focus):
    """Normalize inherited focus state to a valid review focus label."""
    alias_map = {
        "促活": "活跃",
        "拉收": "付费",
        "流失风险": "留存",
    }
    normalized = alias_map.get(raw_focus, raw_focus)
    if normalized in REVIEW_FOCUS_OPTIONS:
        return normalized
    return "综合表现"


def set_review_focus_state(focus_name):
    """Persist the current review focus in business state."""
    set_interaction_state(
        source="活动复盘",
        selected_review_focus=focus_name,
        selected_metric_focus=focus_name,
        selected_metric=FOCUS_DEFAULT_METRIC[focus_name],
    )


def on_review_focus_change():
    """Push the review focus radio selection back into business state."""
    set_review_focus_state(st.session_state.get("review_focus_widget"))


def build_focus_summary(focus_name, result_row, segment_label, review_variant_label):
    """Generate a short analytical summary for the current review focus."""
    if focus_name == "综合表现":
        return (
            f"{review_variant_label} 在 {segment_label} 上的整体表现更适合从“参与、留存、付费”三个方向综合看，"
            f"避免只盯单一指标而忽略方案偏向。"
        )
    if focus_name == "活跃":
        return (
            f"当前方案在活跃侧的主要观察点是参与率 {result_row['participation_rate']:.1%} "
            f"与 DAU提升 {result_row['dau_uplift']:.1%}，更适合判断活动触达是否有效。"
        )
    if focus_name == "留存":
        return (
            f"当前方案在留存侧重点观察 D1留存提升 {result_row['d1_retention_uplift']:.1%} "
            f"与 D7留存提升 {result_row['d7_retention_uplift']:.1%}，可用于判断活动热度是否留得住。"
        )
    if focus_name == "付费":
        return (
            f"当前方案在付费侧重点观察付费转化提升 {result_row['payment_conversion_uplift']:.1%} "
            f"与 ARPPU提升 {result_row['arppu_uplift']:.1%}，可用于判断活动是否带来更强的变现效率。"
        )
    return (
        f"当前方案的奖励成本为 ¥{result_row['reward_cost']:.2f}，通胀风险为 {result_row['inflation_risk']:.1%}，"
        f"成本侧更适合用于判断奖励投放是否仍在可控区间。"
    )


def build_focus_action(focus_name):
    """Generate a focus-specific follow-up recommendation."""
    if focus_name == "综合表现":
        return "建议先把当前方案放回完整经营目标里看，再决定下一轮更该放大活跃、留存还是付费侧收益。"
    if focus_name == "活跃":
        return "建议继续围绕触达频次、回流召回和首日参与链路做二次验证，确认活跃拉升来自真实行为而非短期曝光。"
    if focus_name == "留存":
        return "建议补强中后段目标与连续反馈机制，避免活动热度在首日释放后快速回落。"
    if focus_name == "付费":
        return "建议把奖励节奏与礼包、限时商店或更明确的付费触点联动，继续验证转化深度是否可持续。"
    return "建议继续观察高价值奖励释放节奏，并搭配回收链路控制资源通胀。"


try:
    ab_results_df = load_ab_test_results()
except (FileNotFoundError, ValueError) as exc:
    st.error(f"复盘数据不可用：{exc}")
    st.stop()

render_page_header("活动复盘", "基于活动结果生成复盘结论与后续优化建议。")
block_spacer("sm")
render_analysis_flow(
    "活动复盘",
    caption="沿用前面已选的圈层、配置和对照方案，把结果解释收束到同一条分析链路里。",
)
block_spacer("sm")

event_options = [event_key for event_key in EVENT_ORDER if event_key in ab_results_df["event_name"].unique()]
segment_options = [
    segment_key for segment_key in SEGMENT_ORDER if segment_key in ab_results_df["segment"].unique()
]

if not event_options or not segment_options:
    st.warning("当前暂无可用于活动复盘的数据。")
    st.stop()

active_configuration = st.session_state.get("active_configuration") or st.session_state.get("active_scenario") or {}
default_event = active_configuration.get("event_name") or st.session_state.get("selected_event") or event_options[0]
default_segment = (
    active_configuration.get("target_segment")
    or st.session_state.get("selected_segment")
    or segment_options[0]
)
had_active_configuration = bool(active_configuration)
had_review_pair = (
    st.session_state.get("comparison_baseline") is not None
    and (st.session_state.get("comparison_target") is not None or st.session_state.get("selected_plan") is not None)
)

ensure_interaction_value("selected_event", event_options, default_event)
ensure_interaction_value("selected_segment", segment_options, default_segment)

if had_active_configuration:
    render_status_note("当前复盘延续生效配置与对照关系，可直接切换解读重点。")
else:
    render_status_note("当前未读取到生效配置，复盘先沿用默认活动与圈层。")
block_spacer("sm")

filters = filter_card("复盘筛选", selected=True)
filter_col1, filter_col2, filter_col3 = filters.columns([1, 1, 0.95])

with filter_col1:
    selected_event = st.selectbox(
        "选择活动",
        event_options,
        format_func=get_event_label,
        key="selected_event",
    )

with filter_col2:
    selected_segment = st.selectbox(
        "选择玩家分层",
        segment_options,
        format_func=get_segment_label,
        key="selected_segment",
    )

with filter_col3:
    st.caption("操作")
    st.caption("仅重置当前复盘焦点")
    if st.button("重置复盘焦点", key="reset_review_view", use_container_width=True):
        st.session_state["review_reset_requested"] = True
        st.rerun()

filtered_df = ab_results_df[
    (ab_results_df["event_name"] == selected_event)
    & (ab_results_df["segment"] == selected_segment)
].copy()

if filtered_df.empty:
    render_empty_state(
        "当前暂无复盘结果",
        "当前活动与圈层下暂无可用复盘结果。",
        hint="可切换活动或玩家分层。",
    )
    st.stop()

review_focus_rebuilt = False
if st.session_state.pop("review_reset_requested", False):
    clear_interaction_state(["selected_review_focus"], source="活动复盘")
    st.session_state.pop("review_focus_widget", None)
    st.session_state.pop("pending_review_focus_widget", None)
    review_focus_rebuilt = True

if filtered_df["variant"].nunique() < 2:
    render_empty_state(
        "暂无可复盘对照",
        "当前条件下仅有一个方案结果，暂时无法从对照视角展开复盘。",
        hint="可先前往方案对照确认基准方案与当前关注方案。",
    )
    st.stop()

best_variant_row = select_best_variant(filtered_df)
best_variant_key = best_variant_row["variant"]
review_variant_key = st.session_state.get("comparison_target") or st.session_state.get("selected_plan")
if review_variant_key not in filtered_df["variant"].tolist():
    review_variant_key = best_variant_key

baseline_variant_key = st.session_state.get("comparison_baseline")
if baseline_variant_key not in filtered_df["variant"].tolist() or baseline_variant_key == review_variant_key:
    baseline_variant_key = next(
        (variant for variant in filtered_df["variant"].tolist() if variant != review_variant_key),
        review_variant_key,
    )

review_variant_row = filtered_df.loc[filtered_df["variant"] == review_variant_key].iloc[0]
baseline_variant_row = filtered_df.loc[filtered_df["variant"] == baseline_variant_key].iloc[0]
segment_label = get_segment_label(selected_segment)
review_variant_label = VARIANT_LABELS.get(review_variant_key, review_variant_key)
baseline_variant_label = VARIANT_LABELS.get(baseline_variant_key, baseline_variant_key)
best_variant_label = VARIANT_LABELS.get(best_variant_key, best_variant_key)

inferred_focus = (
    st.session_state.get("selected_review_focus")
    or st.session_state.get("selected_metric_focus")
    or metric_to_review_focus(st.session_state.get("selected_metric"))
    or infer_primary_goal(review_variant_row)
)
ensure_interaction_value("selected_review_focus", REVIEW_FOCUS_OPTIONS, infer_review_focus(inferred_focus))
sync_widget_state("review_focus_widget", REVIEW_FOCUS_OPTIONS, st.session_state["selected_review_focus"])

if not had_review_pair:
    render_status_row("当前未建立明确对照关系，已按默认方案与基准进入复盘。")
elif review_focus_rebuilt:
    render_status_row("当前复盘焦点已恢复为默认视角。")
block_spacer("sm")

focus_card = filter_card("当前关注", selected=True)
focus_col1, focus_col2 = focus_card.columns([1.8, 1.2])

with focus_col1:
    selected_review_focus = st.radio(
        "当前关注",
        REVIEW_FOCUS_OPTIONS,
        horizontal=True,
        key="review_focus_widget",
        on_change=on_review_focus_change,
    )

with focus_col2:
    bridge_card = section_card("回看链路", selected=True)
    with bridge_card:
        st.page_link("pages/3_方案对照.py", label="回到方案对照")
        st.page_link("pages/2_活动配置.py", label="回看活动配置")

selected_metric = FOCUS_DEFAULT_METRIC[selected_review_focus]
set_interaction_state(
    source="活动复盘",
    selected_metric_focus=selected_review_focus,
    selected_metric=selected_metric,
    selected_plan=review_variant_key,
    comparison_target=review_variant_key,
    comparison_baseline=baseline_variant_key,
    selected_review_focus=selected_review_focus,
)

insight_bundle = generate_postmortem_insights(review_variant_row, segment_label)

render_context_bar(
    "当前复盘",
    [
        ("活动", get_event_label(selected_event)),
        ("圈层", segment_label),
        ("方案", review_variant_label),
        ("基准", baseline_variant_label),
        ("焦点", selected_review_focus),
    ],
    caption=(
        f"当前复盘延续上一页的方案对照关系。"
        + (
            f" 当前结果优选仍为 {best_variant_label}。"
            if review_variant_key != best_variant_key
            else f" 当前复盘方案与综合优选 {best_variant_label} 一致。"
        )
    ),
    emphasis="复盘中",
)

block_spacer()
summary_cards = [
    ("综合表现", ["participation_rate", "d7_retention_uplift"], "查看整体解读"),
    ("活跃", ["participation_rate", "dau_uplift"], "查看活跃解读"),
    ("留存", ["d1_retention_uplift", "d7_retention_uplift"], "查看留存解读"),
    ("付费", ["payment_conversion_uplift", "arppu_uplift"], "查看付费解读"),
]
card_columns = st.columns(4)
for column, (focus_name, metric_keys, button_label) in zip(card_columns, summary_cards):
    with column:
        result_card = section_card(
            focus_name,
            caption="切换后，下方解释与建议会同步更新。",
            selected=selected_review_focus == focus_name,
        )
        with result_card:
            render_context_bar(
                "结果摘要",
                [(KPI_LABELS[metric_key], format_value(metric_key, review_variant_row[metric_key])) for metric_key in metric_keys],
                caption=(
                    f"相对 {baseline_variant_label}："
                    + " / ".join(
                        f"{KPI_LABELS[metric_key]} {format_delta(metric_key, review_variant_row[metric_key] - baseline_variant_row[metric_key])}"
                        for metric_key in metric_keys
                    )
                ),
                emphasis="当前焦点" if selected_review_focus == focus_name else "切换关注",
                compact=True,
            )
            if st.button(button_label, key=f"review_focus_{focus_name}", use_container_width=True):
                st.session_state["pending_review_focus_widget"] = focus_name
                set_review_focus_state(focus_name)
                st.rerun()

block_spacer("sm")
cost_card = section_card(
    "成本",
    caption="切换后，下方解释与建议会同步更新。",
    selected=selected_review_focus == "成本",
)
with cost_card:
    render_context_bar(
        "结果摘要",
        [("奖励成本", format_value("reward_cost", review_variant_row["reward_cost"])), ("通胀风险", format_value("inflation_risk", review_variant_row["inflation_risk"]))],
        caption=(
            f"相对 {baseline_variant_label}："
            f"奖励成本 {format_delta('reward_cost', review_variant_row['reward_cost'] - baseline_variant_row['reward_cost'])} / "
            f"通胀风险 {format_delta('inflation_risk', review_variant_row['inflation_risk'] - baseline_variant_row['inflation_risk'])}"
        ),
        emphasis="当前焦点" if selected_review_focus == "成本" else "切换关注",
        compact=True,
    )
    if st.button("查看成本解读", key="review_focus_成本", use_container_width=True):
        st.session_state["pending_review_focus_widget"] = "成本"
        set_review_focus_state("成本")
        st.rerun()

anomaly_markers = []
if review_variant_row["reward_cost"] >= 220:
    anomaly_markers.append(("奖励成本偏高", "成本"))
if review_variant_row["inflation_risk"] >= 0.60:
    anomaly_markers.append(("通胀风险偏高", "成本"))
if review_variant_row["d7_retention_uplift"] < 0.015:
    anomaly_markers.append(("D7留存偏弱", "留存"))
if review_variant_row["payment_conversion_uplift"] >= 0.02 or review_variant_row["arppu_uplift"] >= 0.06:
    anomaly_markers.append(("付费拉动明显", "付费"))
if review_variant_row["participation_rate"] >= 0.30 and review_variant_row["dau_uplift"] >= 0.10:
    anomaly_markers.append(("活跃响应明显", "活跃"))

block_spacer()
marker_card = section_card(
    "结果标记",
    caption="点击结果标记可直接切换复盘解释焦点。",
    selected=True,
)
with marker_card:
    if anomaly_markers:
        marker_cols = st.columns(len(anomaly_markers))
        for column, (label, focus_name) in zip(marker_cols, anomaly_markers):
            with column:
                if st.button(label, key=f"review_marker_{label}", use_container_width=True):
                    st.session_state["pending_review_focus_widget"] = focus_name
                    set_review_focus_state(focus_name)
                    st.rerun()
    else:
        st.caption("当前方案暂无明显结果标记，可继续从上方切换复盘视角。")

block_spacer()
focus_summary_card = section_card(
    "复盘焦点",
    caption=f"当前关注：{selected_review_focus}",
    selected=True,
)
with focus_summary_card:
    focus_metrics = REVIEW_FOCUS_METRICS[selected_review_focus]
    render_context_bar(
        "焦点摘要",
        [(KPI_LABELS[metric_key], format_value(metric_key, review_variant_row[metric_key])) for metric_key in focus_metrics],
        caption=build_focus_summary(selected_review_focus, review_variant_row, segment_label, review_variant_label),
        emphasis=f"当前关注：{selected_review_focus}",
        compact=True,
    )

focus_metric_order = REVIEW_FOCUS_METRICS[selected_review_focus] + [
    metric_key
    for metric_key in [
        "participation_rate",
        "dau_uplift",
        "d1_retention_uplift",
        "d7_retention_uplift",
        "payment_conversion_uplift",
        "arppu_uplift",
        "reward_cost",
        "inflation_risk",
    ]
    if metric_key not in REVIEW_FOCUS_METRICS[selected_review_focus]
]
summary_df = pd.DataFrame(
    {
        "指标": [KPI_LABELS[metric_key] for metric_key in focus_metric_order],
        "当前方案": [format_value(metric_key, review_variant_row[metric_key]) for metric_key in focus_metric_order],
        "相对基准": [
            format_delta(metric_key, review_variant_row[metric_key] - baseline_variant_row[metric_key])
            for metric_key in focus_metric_order
        ],
    }
)
with st.expander("查看详细指标"):
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

focused_conclusions = [build_focus_summary(selected_review_focus, review_variant_row, segment_label, review_variant_label)] + insight_bundle["conclusions"]
focused_actions = [build_focus_action(selected_review_focus)] + insight_bundle["actions"]

block_spacer()
conclusion_card = section_card(
    "复盘结论",
    caption="先看当前关注维度，再补充整体结论。",
    selected=True,
)
with conclusion_card:
    render_compact_list(focused_conclusions[:5])

block_spacer()
action_card = section_card(
    "建议动作",
    caption="建议顺序会随当前关注维度调整。",
    selected=True,
)
with action_card:
    render_compact_list(focused_actions[:4])

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_ab_test_results_data
from src.display_labels import (
    AB_METRIC_LABELS,
    EVENT_ORDER,
    SEGMENT_ORDER,
    get_event_label,
    get_segment_label,
)
from src.ui import (
    apply_axis_format,
    block_spacer,
    clear_interaction_state,
    ensure_comparison_pair,
    ensure_interaction_value,
    filter_card,
    init_page,
    metric_to_review_focus,
    render_analysis_flow,
    render_context_bar,
    render_empty_state,
    render_page_header,
    render_plotly_chart,
    render_status_note,
    render_status_row,
    section_card,
    set_interaction_state,
    style_figure,
    sync_widget_state,
)

VARIANT_LABELS = {"A": "方案A", "B": "方案B"}
FOCUS_OPTIONS = ["综合表现", "活跃", "留存", "付费"]
FOCUS_TO_METRICS = {
    "综合表现": [
        "participation_rate",
        "dau_uplift",
        "d1_retention_uplift",
        "d7_retention_uplift",
        "payment_conversion_uplift",
        "arppu_uplift",
    ],
    "活跃": ["participation_rate", "dau_uplift"],
    "留存": ["d1_retention_uplift", "d7_retention_uplift"],
    "付费": ["payment_conversion_uplift", "arppu_uplift"],
}
FOCUS_TO_PRIMARY_METRIC = {
    "综合表现": "dau_uplift",
    "活跃": "dau_uplift",
    "留存": "d7_retention_uplift",
    "付费": "payment_conversion_uplift",
}


init_page("方案对照")


@st.cache_data
def load_ab_test_results():
    """Load synthetic A/B experiment results."""
    return load_ab_test_results_data()


def get_variant_score(row, metric_columns):
    """Use a simple additive score to compare the two variants."""
    return row[metric_columns].sum()


def infer_goal(row):
    """Infer the strongest business goal from the uplift pattern."""
    goal_scores = {
        "促活": row["participation_rate"] + row["dau_uplift"],
        "留存": row["d1_retention_uplift"] + row["d7_retention_uplift"],
        "拉收": row["payment_conversion_uplift"] + row["arppu_uplift"],
    }
    return max(goal_scores, key=goal_scores.get)


def infer_focus_label(raw_focus):
    """Map inherited state to the comparison focus selector."""
    if raw_focus in FOCUS_OPTIONS:
        return raw_focus
    alias_map = {"促活": "活跃", "拉收": "付费", "成本": "综合表现", "流失风险": "留存"}
    return alias_map.get(raw_focus, "综合表现")


def on_comparison_baseline_change():
    """Push the baseline radio selection back into business state."""
    set_interaction_state(
        source="方案对照",
        comparison_baseline=st.session_state.get("comparison_baseline_widget"),
    )


def on_comparison_target_change():
    """Push the target radio selection back into business state."""
    selected_target = st.session_state.get("comparison_target_widget")
    set_interaction_state(
        source="方案对照",
        comparison_target=selected_target,
        selected_plan=selected_target,
    )


def on_comparison_focus_change():
    """Push the focus radio selection back into business state."""
    set_interaction_state(
        source="方案对照",
        selected_metric_focus=st.session_state.get("comparison_focus_widget"),
    )


try:
    ab_results_df = load_ab_test_results()
except (FileNotFoundError, ValueError) as exc:
    st.error(f"A/B 数据不可用：{exc}")
    st.stop()

render_page_header("方案对照", "对比不同活动方案在目标分层中的关键指标表现。")
block_spacer("sm")
render_analysis_flow(
    "方案对照",
    caption="沿用当前活动与圈层上下文，把方案差异明确为“基准方案 vs 当前关注方案”，再围绕主指标查看差值。",
)
block_spacer("sm")

event_options = [event_key for event_key in EVENT_ORDER if event_key in ab_results_df["event_name"].unique()]
segment_options = [
    segment_key for segment_key in SEGMENT_ORDER if segment_key in ab_results_df["segment"].unique()
]

if not event_options or not segment_options:
    st.warning("当前暂无可用于方案对照的数据。")
    st.stop()

active_configuration = st.session_state.get("active_configuration") or st.session_state.get("active_scenario") or {}
default_event = active_configuration.get("event_name") or st.session_state.get("selected_event") or event_options[0]
default_segment = (
    active_configuration.get("target_segment")
    or st.session_state.get("selected_segment")
    or segment_options[0]
)
had_active_configuration = bool(active_configuration)
had_comparison_pair = (
    st.session_state.get("comparison_baseline") is not None
    and st.session_state.get("comparison_target") is not None
)

ensure_interaction_value("selected_event", event_options, default_event)
ensure_interaction_value("selected_segment", segment_options, default_segment)

if had_active_configuration:
    render_status_note("当前沿用生效配置进入对照，可直接确认基准与关注方案。")
else:
    render_status_note("当前未读取到生效配置，已按默认活动与圈层进入。")
block_spacer("sm")

filters = filter_card("筛选条件", selected=True)
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
    st.caption("仅清空基准与关注方案")
    if st.button("重置对照", key="reset_compare_view", use_container_width=True):
        st.session_state["compare_reset_requested"] = True
        st.rerun()

filtered_df = ab_results_df[
    (ab_results_df["event_name"] == selected_event)
    & (ab_results_df["segment"] == selected_segment)
].copy()

if filtered_df.empty:
    render_empty_state(
        "当前暂无对照结果",
        "当前活动与圈层下暂无方案结果。",
        hint="可切换活动或玩家分层。",
    )
    st.stop()

if filtered_df["variant"].nunique() < 2:
    render_empty_state(
        "暂无可对照方案",
        "当前条件下仅有一个方案结果，暂时无法建立基准方案与当前关注方案。",
        hint="可切换活动或玩家分层。",
    )
    st.stop()

compare_pair_rebuilt = False
if st.session_state.pop("compare_reset_requested", False):
    clear_interaction_state(
        ["comparison_baseline", "comparison_target", "selected_plan"],
        source="方案对照",
    )
    st.session_state.pop("comparison_baseline_widget", None)
    st.session_state.pop("comparison_target_widget", None)
    st.session_state.pop("pending_comparison_baseline_widget", None)
    st.session_state.pop("pending_comparison_target_widget", None)
    compare_pair_rebuilt = True

filtered_df["variant_label"] = filtered_df["variant"].map(VARIANT_LABELS).fillna("未知方案")
metric_columns = list(AB_METRIC_LABELS.keys())

scored_df = filtered_df.copy()
scored_df["overall_score"] = scored_df.apply(lambda row: get_variant_score(row, metric_columns), axis=1)
best_variant_row = scored_df.sort_values("overall_score", ascending=False).iloc[0]
best_variant = best_variant_row["variant"]
best_variant_label = VARIANT_LABELS.get(best_variant, best_variant)
best_goal = infer_goal(best_variant_row)

focus_default = (
    active_configuration.get("metric_focus")
    or st.session_state.get("selected_metric_focus")
    or metric_to_review_focus(st.session_state.get("selected_metric"))
)
ensure_interaction_value("selected_metric_focus", FOCUS_OPTIONS, infer_focus_label(focus_default))

focus_card = filter_card("比较焦点", selected=True)
focus_col1, focus_col2, focus_col3 = focus_card.columns([1.2, 1.2, 2.2])

baseline_default = filtered_df["variant"].tolist()[0]
target_default = best_variant
baseline_variant, target_variant = ensure_comparison_pair(
    filtered_df["variant"].tolist(),
    preferred_baseline=baseline_default,
    preferred_target=target_default,
)
variant_options = filtered_df["variant"].tolist()
sync_widget_state("comparison_baseline_widget", variant_options, baseline_variant)
sync_widget_state("comparison_target_widget", variant_options, target_variant)
if st.session_state["comparison_target_widget"] == st.session_state["comparison_baseline_widget"]:
    st.session_state["comparison_target_widget"] = next(
        (variant for variant in variant_options if variant != st.session_state["comparison_baseline_widget"]),
        st.session_state["comparison_baseline_widget"],
    )
sync_widget_state("comparison_focus_widget", FOCUS_OPTIONS, st.session_state["selected_metric_focus"])

with focus_col1:
    baseline_variant = st.radio(
        "基准方案",
        variant_options,
        format_func=lambda variant_key: VARIANT_LABELS.get(variant_key, variant_key),
        horizontal=True,
        key="comparison_baseline_widget",
        on_change=on_comparison_baseline_change,
    )

with focus_col2:
    target_variant = st.radio(
        "当前关注方案",
        variant_options,
        format_func=lambda variant_key: VARIANT_LABELS.get(variant_key, variant_key),
        horizontal=True,
        key="comparison_target_widget",
        on_change=on_comparison_target_change,
    )

with focus_col3:
    selected_metric_focus = st.radio(
        "当前主指标",
        FOCUS_OPTIONS,
        horizontal=True,
        key="comparison_focus_widget",
        on_change=on_comparison_focus_change,
    )

if target_variant == baseline_variant:
    target_variant = next((variant for variant in variant_options if variant != baseline_variant), baseline_variant)

if not had_comparison_pair or compare_pair_rebuilt:
    render_status_row("当前对照已恢复为默认基准与关注方案。")
    block_spacer("sm")

ordered_focus_metrics = FOCUS_TO_METRICS[selected_metric_focus] + [
    metric_name for metric_name in metric_columns if metric_name not in FOCUS_TO_METRICS[selected_metric_focus]
]
selected_metric = active_configuration.get("focus_metric")
if selected_metric not in ordered_focus_metrics:
    selected_metric = FOCUS_TO_PRIMARY_METRIC[selected_metric_focus]

baseline_row = scored_df.loc[scored_df["variant"] == baseline_variant].iloc[0]
target_row = scored_df.loc[scored_df["variant"] == target_variant].iloc[0]
baseline_label = VARIANT_LABELS.get(baseline_variant, baseline_variant)
target_label = VARIANT_LABELS.get(target_variant, target_variant)
selected_metric_label = AB_METRIC_LABELS[selected_metric]
selected_metric_diff = target_row[selected_metric] - baseline_row[selected_metric]
score_diff = target_row["overall_score"] - baseline_row["overall_score"]

set_interaction_state(
    source="方案对照",
    selected_metric_focus=selected_metric_focus,
    selected_metric=selected_metric,
    comparison_baseline=baseline_variant,
    comparison_target=target_variant,
    selected_plan=target_variant,
    selected_review_focus=metric_to_review_focus(selected_metric),
)

render_context_bar(
    "当前对照",
    [
        ("范围", f"{get_event_label(selected_event)} / {get_segment_label(selected_segment)}"),
        ("基准", baseline_label),
        ("关注", target_label),
        ("焦点", selected_metric_focus),
    ],
    caption=f"当前综合优选为 {best_variant_label}，适配目标偏向 {best_goal}。",
    emphasis="对照中",
)

block_spacer()
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
kpi_col1.metric("基准方案", baseline_label)
kpi_col2.metric("当前关注方案", target_label)
kpi_col3.metric(selected_metric_label, f"{target_row[selected_metric]:.1%}", delta=f"{selected_metric_diff:+.1%}")
kpi_col4.metric("综合得分差值", f"{target_row['overall_score']:.1%}", delta=f"{score_diff:+.1%}")

block_spacer()
variant_rows = [row for _, row in scored_df.sort_values("variant").iterrows()]
plan_cols = st.columns(len(variant_rows))
for column, row in zip(plan_cols, variant_rows):
    variant_key = row["variant"]
    variant_label = VARIANT_LABELS.get(variant_key, variant_key)
    top_metric_key = row[ordered_focus_metrics].idxmax()
    with column:
        plan_card = section_card(
            variant_label,
            caption=f"当前焦点维度下最强单项：{AB_METRIC_LABELS[top_metric_key]} {row[top_metric_key]:.1%}",
            selected=variant_key in {baseline_variant, target_variant},
            muted=variant_key not in {baseline_variant, target_variant},
        )
        with plan_card:
            render_context_bar(
                "方案状态",
                [
                    ("当前主指标", f"{selected_metric_label} {row[selected_metric]:.1%}"),
                    ("平均提升幅度", f"{row[metric_columns].mean():.1%}"),
                    ("综合得分", f"{row['overall_score']:.1%}"),
                ],
                caption=(
                    "当前用于比较基准。"
                    if variant_key == baseline_variant
                    else "当前作为重点对照方案。"
                    if variant_key == target_variant
                    else "可切换为基准或关注方案。"
                ),
                emphasis=(
                    "基准方案"
                    if variant_key == baseline_variant
                    else "当前关注"
                    if variant_key == target_variant
                    else "可选方案"
                ),
                compact=True,
            )
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button(
                    "设为基准",
                    key=f"set_baseline_{variant_key}",
                    use_container_width=True,
                    disabled=variant_key == baseline_variant,
                ):
                    st.session_state["pending_comparison_baseline_widget"] = variant_key
                    set_interaction_state(source="方案对照", comparison_baseline=variant_key)
                    st.rerun()
            with action_col2:
                if st.button(
                    "设为关注方案",
                    key=f"set_target_{variant_key}",
                    use_container_width=True,
                    disabled=variant_key == target_variant,
                ):
                    if variant_key == baseline_variant:
                        replacement_baseline = (
                            target_variant
                            if target_variant != variant_key
                            else next(
                                (variant for variant in variant_options if variant != variant_key),
                                baseline_variant,
                            )
                        )
                        st.session_state["pending_comparison_baseline_widget"] = replacement_baseline
                        set_interaction_state(source="方案对照", comparison_baseline=replacement_baseline)
                    st.session_state["pending_comparison_target_widget"] = variant_key
                    set_interaction_state(source="方案对照", comparison_target=variant_key, selected_plan=variant_key)
                    st.rerun()

block_spacer()
comparison_table = pd.DataFrame(
    {
        "对照角色": ["基准方案", "当前关注方案"],
        "方案": [baseline_label, target_label],
        **{
            AB_METRIC_LABELS[metric_name]: [
                f"{baseline_row[metric_name]:.1%}",
                f"{target_row[metric_name]:.1%}",
            ]
            for metric_name in ordered_focus_metrics
        },
    }
)
metrics_card = section_card(
    "指标对比",
    caption=f"当前主指标为 {selected_metric_focus}，相关指标已前置排序。",
    selected=True,
)
metrics_card.dataframe(comparison_table, use_container_width=True, hide_index=True)

block_spacer()
chart_df = pd.DataFrame(
    [
        {
            "variant": baseline_variant,
            "variant_label": baseline_label,
            "metric_key": metric_name,
            "metric_value": baseline_row[metric_name],
        }
        for metric_name in ordered_focus_metrics
    ]
    + [
        {
            "variant": target_variant,
            "variant_label": target_label,
            "metric_key": metric_name,
            "metric_value": target_row[metric_name],
        }
        for metric_name in ordered_focus_metrics
    ]
)
chart_df["指标"] = chart_df["metric_key"].map(AB_METRIC_LABELS)
metric_order = [AB_METRIC_LABELS[metric_key] for metric_key in ordered_focus_metrics]

fig = px.bar(
    chart_df,
    x="metric_value",
    y="指标",
    color="variant_label",
    barmode="group",
    orientation="h",
    labels={"variant_label": "方案", "metric_value": "提升幅度"},
    category_orders={"指标": list(reversed(metric_order))},
    text_auto=".1%",
)
fig.update_layout(
    xaxis_title="提升幅度",
    yaxis_title="",
    legend_title_text="",
    bargap=0.28,
    height=390,
)
apply_axis_format(fig, "x", "percent")
fig.update_xaxes(zeroline=True)
fig.update_traces(textposition="outside", cliponaxis=False)
fig = style_figure(fig, show_legend=True)
for trace in fig.data:
    if trace.name == target_label:
        trace.opacity = 1
        trace.marker.line.width = 2.4
    else:
        trace.opacity = 0.74
        trace.marker.line.width = 1.2
chart_card = section_card(
    "对比图",
    caption=f"{selected_metric_focus} 相关指标已前置，当前关注方案 {target_label} 保持高亮。",
    selected=True,
)
render_plotly_chart(chart_card, fig)

block_spacer()
selected_direction = "领先" if selected_metric_diff >= 0 else "落后"
conclusion_card = section_card("方案结论", selected=True)
conclusion_card.write(
    f"{get_event_label(selected_event)} / {get_segment_label(selected_segment)}："
    f"当前重点在比较 {selected_metric_focus}，以 {baseline_label} 为基准，"
    f"{target_label} 在 {selected_metric_label} 上{selected_direction}"
    f" {baseline_label} {abs(selected_metric_diff):.1%}。"
    f"当前综合优选仍为 {best_variant_label}，建议优先用于 {best_goal} 目标。"
)

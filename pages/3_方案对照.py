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
    apply_dashboard_theme,
    block_spacer,
    configure_page,
    filter_card,
    render_page_header,
    render_plotly_chart,
    section_card,
    style_figure,
)

VARIANT_LABELS = {"A": "方案A", "B": "方案B"}


configure_page("方案对照")
apply_dashboard_theme()


@st.cache_data
def load_ab_test_results():
    """Load synthetic A/B experiment results."""
    return load_ab_test_results_data()


try:
    ab_results_df = load_ab_test_results()
except (FileNotFoundError, ValueError) as exc:
    st.error(f"A/B 数据不可用：{exc}")
    st.stop()

render_page_header("方案对照", "对比不同活动方案在目标分层中的关键指标表现。")

# Use Chinese labels in the UI while keeping filters on the original values.
event_options = [event_key for event_key in EVENT_ORDER if event_key in ab_results_df["event_name"].unique()]
segment_options = [
    segment_key for segment_key in SEGMENT_ORDER if segment_key in ab_results_df["segment"].unique()
]

if not event_options or not segment_options:
    st.warning("当前暂无可用于方案对照的数据。")
    st.stop()

filters = filter_card("筛选条件")
filter_col1, filter_col2 = filters.columns(2)

with filter_col1:
    selected_event = st.selectbox(
        "选择活动",
        event_options,
        format_func=get_event_label,
    )

with filter_col2:
    selected_segment = st.selectbox(
        "选择玩家分层",
        segment_options,
        format_func=get_segment_label,
    )

filtered_df = ab_results_df[
    (ab_results_df["event_name"] == selected_event)
    & (ab_results_df["segment"] == selected_segment)
].copy()

if filtered_df.empty:
    st.warning("当前筛选条件下暂无对照数据，可切换其他活动或分层。")
    st.stop()

filtered_df["variant_label"] = filtered_df["variant"].map(VARIANT_LABELS).fillna("未知方案")

metric_columns = list(AB_METRIC_LABELS.keys())
display_table = filtered_df[["variant_label"] + metric_columns].copy()
display_table["variant_label"] = display_table["variant_label"]
for metric_name in metric_columns:
    display_table[metric_name] = display_table[metric_name].map(lambda value: f"{value:.1%}")
display_table = display_table.rename(columns={"variant_label": "方案", **AB_METRIC_LABELS})


def get_variant_score(row):
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


scored_df = filtered_df.copy()
scored_df["overall_score"] = scored_df.apply(get_variant_score, axis=1)
best_variant_row = scored_df.sort_values("overall_score", ascending=False).iloc[0]
best_variant_label = VARIANT_LABELS.get(best_variant_row["variant"], "未知方案")
best_goal = infer_goal(best_variant_row)
top_metric_key = best_variant_row[metric_columns].idxmax()
average_uplift = best_variant_row[metric_columns].mean()

block_spacer()
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
kpi_col1.metric("当前优选方案", best_variant_label)
kpi_col2.metric("适配目标", best_goal)
kpi_col3.metric("平均提升幅度", f"{average_uplift:.1%}")
kpi_col4.metric("最高单项提升", f"{AB_METRIC_LABELS[top_metric_key]} {best_variant_row[top_metric_key]:.1%}")
block_spacer()

# Show a compact metric table for the selected A/B pair.
metrics_card = section_card("指标对比")
metrics_card.dataframe(display_table, use_container_width=True, hide_index=True)
block_spacer()

chart_df = filtered_df.melt(
    id_vars="variant_label",
    value_vars=metric_columns,
    var_name="metric_key",
    value_name="metric_value",
)
chart_df["指标"] = chart_df["metric_key"].map(AB_METRIC_LABELS)
metric_order = [AB_METRIC_LABELS[metric_key] for metric_key in metric_columns]

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
    height=360,
)
apply_axis_format(fig, "x", "percent")
fig.update_xaxes(zeroline=True)
fig.update_traces(textposition="outside", cliponaxis=False)
chart_card = section_card("对比图")
render_plotly_chart(chart_card, style_figure(fig, show_legend=True))

block_spacer()
conclusion_card = section_card("方案结论")
conclusion_card.write(
    f"{get_event_label(selected_event)} / {get_segment_label(selected_segment)}："
    f"{best_variant_label}更优，建议优先用于{best_goal}目标。"
)

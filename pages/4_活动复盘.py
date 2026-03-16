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
from src.insight_generator import generate_postmortem_insights, select_best_variant
from src.ui import (
    apply_dashboard_theme,
    block_spacer,
    configure_page,
    filter_card,
    render_compact_list,
    render_page_header,
    render_status_row,
    section_card,
)

KPI_LABELS = {
    **AB_METRIC_LABELS,
    "reward_cost": "奖励成本",
    "inflation_risk": "通胀风险",
}
VARIANT_LABELS = {"A": "方案A", "B": "方案B"}


configure_page("活动复盘")
apply_dashboard_theme()


@st.cache_data
def load_ab_test_results():
    """Load synthetic A/B results for postmortem analysis."""
    return load_ab_test_results_data()


try:
    ab_results_df = load_ab_test_results()
except (FileNotFoundError, ValueError) as exc:
    st.error(f"复盘数据不可用：{exc}")
    st.stop()

# Build a simple postmortem view driven by rule-based insights.
render_page_header("活动复盘", "基于活动结果生成复盘结论与后续优化建议。")

filters = filter_card()
filter_col1, filter_col2 = filters.columns(2)

event_options = [event_key for event_key in EVENT_ORDER if event_key in ab_results_df["event_name"].unique()]
segment_options = [
    segment_key for segment_key in SEGMENT_ORDER if segment_key in ab_results_df["segment"].unique()
]

if not event_options or not segment_options:
    st.warning("当前暂无可用于活动复盘的数据。")
    st.stop()

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
    st.warning("当前筛选条件下暂无复盘数据，可切换其他活动或分层。")
    st.stop()

best_variant_row = select_best_variant(filtered_df)
segment_label = get_segment_label(selected_segment)
insight_bundle = generate_postmortem_insights(best_variant_row, segment_label)

block_spacer()
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
kpi_col1.metric("参与率", f"{best_variant_row['participation_rate']:.1%}")
kpi_col2.metric("DAU提升", f"{best_variant_row['dau_uplift']:.1%}")
kpi_col3.metric("D1留存提升", f"{best_variant_row['d1_retention_uplift']:.1%}")
kpi_col4.metric("D7留存提升", f"{best_variant_row['d7_retention_uplift']:.1%}")

kpi_col5, kpi_col6, kpi_col7, kpi_col8 = st.columns(4)
kpi_col5.metric("付费转化提升", f"{best_variant_row['payment_conversion_uplift']:.1%}")
kpi_col6.metric("ARPPU提升", f"{best_variant_row['arppu_uplift']:.1%}")
kpi_col7.metric("奖励成本", f"¥{best_variant_row['reward_cost']:.2f}")
kpi_col8.metric("通胀风险", f"{best_variant_row['inflation_risk']:.1%}")

block_spacer()
render_status_row(
    f"当前结果：{get_event_label(selected_event)} / {segment_label} / "
    f"{VARIANT_LABELS.get(best_variant_row['variant'], best_variant_row['variant'])}"
)

summary_df = pd.DataFrame(
    {
        "指标": list(KPI_LABELS.values()),
        "数值": [
            f"{best_variant_row['participation_rate']:.1%}",
            f"{best_variant_row['dau_uplift']:.1%}",
            f"{best_variant_row['d1_retention_uplift']:.1%}",
            f"{best_variant_row['d7_retention_uplift']:.1%}",
            f"{best_variant_row['payment_conversion_uplift']:.1%}",
            f"{best_variant_row['arppu_uplift']:.1%}",
            f"¥{best_variant_row['reward_cost']:.2f}",
            f"{best_variant_row['inflation_risk']:.1%}",
        ],
    }
)
with st.expander("查看详细指标"):
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

block_spacer()
conclusion_card = section_card("复盘结论")
with conclusion_card:
    render_compact_list(insight_bundle["conclusions"])

block_spacer()
action_card = section_card("建议动作")
with action_card:
    render_compact_list(insight_bundle["actions"])

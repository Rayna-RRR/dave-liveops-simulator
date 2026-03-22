import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_players_data
from src.display_labels import SEGMENT_ORDER, get_segment_label
from src.ui import (
    apply_axis_format,
    block_spacer,
    clear_interaction_state,
    ensure_interaction_value,
    filter_card,
    init_page,
    metric_to_review_focus,
    render_analysis_flow,
    render_context_bar,
    render_status_note,
    render_status_row,
    render_page_header,
    render_plotly_chart,
    section_card,
    set_interaction_state,
    style_figure,
    sync_widget_state,
)


init_page("用户分层")


@st.cache_data
def load_players():
    """Load synthetic player data for segment analysis."""
    return load_players_data()


try:
    players_df = load_players()
except (FileNotFoundError, ValueError) as exc:
    st.error(f"玩家数据不可用：{exc}")
    st.stop()

# Build segment-level metrics with simple groupby logic.
segment_summary = (
    players_df.groupby("segment", as_index=False)
    .agg(
        total_players=("player_id", "count"),
        payer_rate=("is_payer", "mean"),
        average_total_payment=("total_payment", "mean"),
        average_session_minutes=("avg_session_minutes", "mean"),
        average_churn_risk=("churn_risk_score", "mean"),
    )
)
segment_summary["segment"] = pd.Categorical(
    segment_summary["segment"],
    categories=SEGMENT_ORDER,
    ordered=True,
)
segment_summary = segment_summary.sort_values("segment").reset_index(drop=True)
segment_summary["segment_label"] = segment_summary["segment"].apply(get_segment_label)

if segment_summary.empty:
    st.warning("当前暂无可展示的玩家分层数据。")
    st.stop()

SEGMENT_METRICS = {
    "total_players": {"label": "玩家数", "kind": "count", "chart_title": "玩家数"},
    "payer_rate": {"label": "付费率", "kind": "percent", "chart_title": "付费率"},
    "average_total_payment": {"label": "累计付费", "kind": "currency", "chart_title": "累计付费"},
    "average_session_minutes": {"label": "活跃时长", "kind": "minutes", "chart_title": "活跃时长"},
    "average_churn_risk": {"label": "流失风险", "kind": "percent", "chart_title": "流失风险"},
}
FOCUS_OPTIONS = ["规模", "活跃", "付费", "流失风险"]
FOCUS_TO_PRIMARY_METRIC = {
    "规模": "total_players",
    "活跃": "average_session_minutes",
    "付费": "average_total_payment",
    "流失风险": "average_churn_risk",
}
FOCUS_TO_RELATED_METRICS = {
    "规模": ["total_players", "average_session_minutes"],
    "活跃": ["average_session_minutes", "total_players"],
    "付费": ["average_total_payment", "payer_rate"],
    "流失风险": ["average_churn_risk", "average_session_minutes"],
}
FOCUS_EXPLANATIONS = {
    "规模": "用于判断当前圈层是否值得作为重点经营对象，关注体量与后续承接空间。",
    "活跃": "用于观察该圈层在活动触达后的行为响应潜力，优先看活跃时长与可触达规模。",
    "付费": "用于判断该圈层是否更适合作为拉收对象，优先看累计付费与付费率。",
    "流失风险": "用于识别需要优先召回或留存修复的人群，优先看流失风险与活跃下滑迹象。",
}


def format_metric_value(metric_key, value):
    """Render a metric value in the page's local format."""
    metric_kind = SEGMENT_METRICS[metric_key]["kind"]
    if metric_kind == "percent":
        return f"{value:.1%}"
    if metric_kind == "currency":
        return f"¥{value:,.2f}"
    if metric_kind == "minutes":
        return f"{value:,.1f} 分钟"
    return f"{value:,.0f}"


def format_metric_gap(metric_key, value):
    """Format a signed gap against the overall reference."""
    metric_kind = SEGMENT_METRICS[metric_key]["kind"]
    if metric_kind == "percent":
        return f"{value:+.1%}"
    if metric_kind == "currency":
        return f"¥{value:+,.2f}"
    if metric_kind == "minutes":
        return f"{value:+,.1f} 分钟"
    return f"{value:+,.0f}"


def make_bar_chart(dataframe, metric_key, selected_segment_key, *, height=300):
    """Create consistent segment charts with a selected segment highlight."""
    fig = px.bar(dataframe, x="segment_label", y=metric_key, text_auto=False)
    fig.update_layout(xaxis_title="", yaxis_title="", height=height)
    metric_kind = SEGMENT_METRICS[metric_key]["kind"]

    if metric_kind == "percent":
        fig.update_traces(texttemplate="%{y:.1%}")
        apply_axis_format(fig, "y", "percent")
    elif metric_kind == "currency":
        fig.update_traces(texttemplate="¥%{y:,.2f}")
        apply_axis_format(fig, "y", "currency")
    elif metric_kind == "minutes":
        fig.update_traces(texttemplate="%{y:.1f} 分钟")
        apply_axis_format(fig, "y", "minutes")
    else:
        fig.update_traces(texttemplate="%{y:,.0f}")
        apply_axis_format(fig, "y", "count")

    selected_index = None
    segment_keys = dataframe["segment"].astype(str).tolist()
    if selected_segment_key in segment_keys:
        selected_index = segment_keys.index(selected_segment_key)

    hover_template = "%{x}<br>%{y:,.0f}<extra></extra>"
    if metric_kind == "percent":
        hover_template = "%{x}<br>%{y:.1%}<extra></extra>"
    elif metric_kind == "currency":
        hover_template = "%{x}<br>¥%{y:,.2f}<extra></extra>"
    elif metric_kind == "minutes":
        hover_template = "%{x}<br>%{y:.1f} 分钟<extra></extra>"

    fig.update_traces(
        textposition="outside",
        cliponaxis=False,
        selectedpoints=[selected_index] if selected_index is not None else None,
        customdata=dataframe[["segment"]].to_numpy(),
        hovertemplate=hover_template,
    )
    return style_figure(fig)


render_page_header("用户分层", "通过玩家分层识别促活、留存与召回的重点对象。")
block_spacer("sm")
render_analysis_flow(
    "用户分层",
    caption="先确定当前最值得分析的玩家圈层，再把这个上下文带到后续配置、对照与复盘页面。",
)
block_spacer("sm")

segment_options = segment_summary["segment"].astype(str).tolist()
default_segment = segment_summary.sort_values("total_players", ascending=False).iloc[0]["segment"]
if st.session_state.pop("reset_segment_requested", False):
    clear_interaction_state(
        ["selected_segment", "selected_metric_focus", "selected_metric", "selected_review_focus"],
        source="用户分层",
    )
    st.session_state.pop("segment_widget", None)
    st.session_state.pop("segment_focus_widget", None)
segment_preselected = st.session_state.get("selected_segment") in segment_options
focus_preselected = st.session_state.get("selected_metric_focus") in FOCUS_OPTIONS
ensure_interaction_value("selected_segment", segment_options, default_segment)
default_focus = st.session_state.get("selected_metric_focus")
if default_focus not in FOCUS_OPTIONS:
    default_focus = metric_to_review_focus(st.session_state.get("selected_metric"))
    if default_focus == "付费":
        default_focus = "付费"
    elif default_focus == "活跃":
        default_focus = "活跃"
    elif default_focus == "留存":
        default_focus = "流失风险"
    elif default_focus == "成本":
        default_focus = "流失风险"
    else:
        default_focus = "规模"
ensure_interaction_value("selected_metric_focus", FOCUS_OPTIONS, default_focus)
ensure_interaction_value(
    "selected_metric",
    list(SEGMENT_METRICS.keys()),
    FOCUS_TO_PRIMARY_METRIC[st.session_state["selected_metric_focus"]],
)
sync_widget_state("segment_widget", segment_options, st.session_state["selected_segment"])
sync_widget_state("segment_focus_widget", FOCUS_OPTIONS, st.session_state["selected_metric_focus"])

if not segment_preselected or not focus_preselected:
    render_status_note("当前已按默认圈层进入，可继续细看，或直接进入活动配置。")
else:
    render_status_row("当前选择会延续到后续页面。")
block_spacer("sm")

selector_card = filter_card("当前分析焦点", selected=True)
selector_col1, selector_col2, selector_col3 = selector_card.columns([2.8, 2.3, 1.1])

with selector_col1:
    selected_segment = st.radio(
        "当前聚焦圈层",
        segment_options,
        format_func=get_segment_label,
        horizontal=True,
        key="segment_widget",
    )

with selector_col2:
    selected_metric_focus = st.radio(
        "当前指标焦点",
        FOCUS_OPTIONS,
        horizontal=True,
        key="segment_focus_widget",
    )

with selector_col3:
    st.caption("操作")
    st.caption("仅重置本页圈层与焦点")
    if st.button("重置分层筛选", key="reset_segment_focus", use_container_width=True):
        st.session_state["reset_segment_requested"] = True
        st.rerun()

selected_metric_focus = selected_metric_focus or st.session_state["selected_metric_focus"]
selected_metric = FOCUS_TO_PRIMARY_METRIC[selected_metric_focus]
set_interaction_state(
    source="用户分层",
    selected_segment=selected_segment,
    selected_metric_focus=selected_metric_focus,
    selected_metric=selected_metric,
    selected_review_focus=metric_to_review_focus(selected_metric),
)

selected_segment_row = segment_summary.loc[segment_summary["segment"] == selected_segment].iloc[0]
selected_segment_label = get_segment_label(selected_segment)
selected_metric_label = SEGMENT_METRICS[selected_metric]["label"]

total_players = len(players_df)
payer_rate = players_df["is_payer"].mean()
average_total_payment = players_df["total_payment"].mean()
average_session_minutes = players_df["avg_session_minutes"].mean()
average_churn_risk = players_df["churn_risk_score"].mean()
overall_values = {
    "total_players": total_players,
    "payer_rate": payer_rate,
    "average_total_payment": average_total_payment,
    "average_session_minutes": average_session_minutes,
    "average_churn_risk": average_churn_risk,
}
analysis_reference_values = {
    **overall_values,
    "total_players": segment_summary["total_players"].mean(),
}

render_context_bar(
    "当前分析",
    [
        ("圈层", selected_segment_label),
        ("焦点", selected_metric_focus),
        ("阶段", "分层分析"),
    ],
    caption="当前圈层会继续带入活动配置、方案对照与活动复盘。",
    emphasis="分析入口",
)
block_spacer()

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
kpi_col1.metric(
    "总玩家数",
    f"{total_players:,}",
    delta=f"{selected_segment_label} {selected_segment_row['total_players']:,}",
)
kpi_col2.metric(
    "付费率",
    f"{payer_rate:.1%}",
    delta=format_metric_gap("payer_rate", selected_segment_row["payer_rate"] - payer_rate),
)
kpi_col3.metric(
    "平均累计付费",
    f"¥{average_total_payment:,.2f}",
    delta=format_metric_gap(
        "average_total_payment",
        selected_segment_row["average_total_payment"] - average_total_payment,
    ),
)
kpi_col4.metric(
    "平均单次时长",
    f"{average_session_minutes:,.1f}",
    delta=format_metric_gap(
        "average_session_minutes",
        selected_segment_row["average_session_minutes"] - average_session_minutes,
    ),
)
block_spacer()

focus_card = section_card(
    "圈层聚焦",
    caption="圈层摘要会随当前圈层与分析焦点同步更新。",
    selected=True,
)
with focus_card:
    metric_ranks = (
        segment_summary[["segment", selected_metric]]
        .sort_values(selected_metric, ascending=False)
        .reset_index(drop=True)
    )
    selected_rank = (
        metric_ranks.index[metric_ranks["segment"] == selected_segment].tolist()[0] + 1
    )
    selected_metric_value = selected_segment_row[selected_metric]
    reference_value = analysis_reference_values[selected_metric]
    gap_value = selected_metric_value - reference_value
    direction = "高于" if gap_value >= 0 else "低于"
    if selected_metric == "total_players":
        focus_caption = (
            f"{selected_segment_label} 当前占总玩家 {selected_segment_row['total_players'] / total_players:.1%}，"
            f"圈层规模位列第 {selected_rank}。"
        )
    else:
        focus_caption = (
            f"{selected_segment_label} 在 {selected_metric_label} 上位列第 {selected_rank}，"
            f"{direction}整体参考 {format_metric_gap(selected_metric, gap_value)}。"
        )

    focus_rows = []
    ordered_metric_keys = FOCUS_TO_RELATED_METRICS[selected_metric_focus] + [
        metric_key
        for metric_key in SEGMENT_METRICS
        if metric_key not in FOCUS_TO_RELATED_METRICS[selected_metric_focus]
    ]
    for metric_key in ordered_metric_keys:
        current_value = selected_segment_row[metric_key]
        if metric_key == "total_players":
            reference_text = f"占总玩家 {current_value / total_players:.1%}"
            observation = f"当前圈层规模位列第{selected_rank}" if metric_key == selected_metric else "用于衡量圈层体量"
        else:
            reference_text = format_metric_value(metric_key, overall_values[metric_key])
            gap = current_value - overall_values[metric_key]
            observation = f"{'高于' if gap >= 0 else '低于'}整体 {format_metric_gap(metric_key, gap)}"

        focus_rows.append(
            {
                "分析项": SEGMENT_METRICS[metric_key]["label"],
                "当前圈层": format_metric_value(metric_key, current_value),
                "整体参考": reference_text,
                "观察": observation,
            }
        )

    render_context_bar(
        "当前聚焦摘要",
        [
            ("圈层", selected_segment_label),
            ("焦点", selected_metric_focus),
            ("排序", f"第 {selected_rank} 位"),
        ],
        caption=f"{focus_caption} {FOCUS_EXPLANATIONS[selected_metric_focus]}",
        emphasis="选中状态",
        compact=True,
    )
    block_spacer("sm")
    st.dataframe(pd.DataFrame(focus_rows), use_container_width=True, hide_index=True)

block_spacer("sm")
top_chart_col1, top_chart_col2 = st.columns(2)

with top_chart_col1:
    player_count_card = section_card(
        SEGMENT_METRICS["total_players"]["chart_title"],
        caption="上方切换焦点后，图表会同步调整强调。",
        selected="total_players" in FOCUS_TO_RELATED_METRICS[selected_metric_focus],
    )
    render_plotly_chart(
        player_count_card,
        make_bar_chart(segment_summary, "total_players", selected_segment),
    )

with top_chart_col2:
    payer_card = section_card(
        SEGMENT_METRICS["payer_rate"]["chart_title"],
        selected="payer_rate" in FOCUS_TO_RELATED_METRICS[selected_metric_focus],
    )
    render_plotly_chart(
        payer_card,
        make_bar_chart(segment_summary, "payer_rate", selected_segment),
    )

block_spacer("sm")
bottom_chart_col1, bottom_chart_col2 = st.columns(2)

with bottom_chart_col1:
    payment_card = section_card(
        SEGMENT_METRICS["average_total_payment"]["chart_title"],
        selected="average_total_payment" in FOCUS_TO_RELATED_METRICS[selected_metric_focus],
    )
    render_plotly_chart(
        payment_card,
        make_bar_chart(segment_summary, "average_total_payment", selected_segment),
    )

with bottom_chart_col2:
    session_card = section_card(
        SEGMENT_METRICS["average_session_minutes"]["chart_title"],
        selected="average_session_minutes" in FOCUS_TO_RELATED_METRICS[selected_metric_focus],
    )
    render_plotly_chart(
        session_card,
        make_bar_chart(segment_summary, "average_session_minutes", selected_segment),
    )

block_spacer("sm")
churn_card = section_card(
    SEGMENT_METRICS["average_churn_risk"]["chart_title"],
    caption=f"当前固定高亮：{selected_segment_label}",
    selected="average_churn_risk" in FOCUS_TO_RELATED_METRICS[selected_metric_focus],
)
render_plotly_chart(
    churn_card,
    make_bar_chart(segment_summary, "average_churn_risk", selected_segment, height=320),
)

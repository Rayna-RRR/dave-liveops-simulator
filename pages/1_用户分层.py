import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_loader import load_players_data
from src.display_labels import SEGMENT_ORDER, get_segment_label
from src.ui import (
    apply_axis_format,
    apply_dashboard_theme,
    block_spacer,
    configure_page,
    render_page_header,
    render_plotly_chart,
    section_card,
    style_figure,
)


configure_page("用户分层")
apply_dashboard_theme()


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
segment_summary = segment_summary.sort_values("segment")
segment_summary["segment_label"] = segment_summary["segment"].apply(get_segment_label)

if segment_summary.empty:
    st.warning("当前暂无可展示的玩家分层数据。")
    st.stop()

render_page_header("用户分层", "通过玩家分层识别促活、留存与召回的重点对象。")
block_spacer()

# Show top-line KPIs for a quick business read.
total_players = len(players_df)
payer_rate = players_df["is_payer"].mean()
average_total_payment = players_df["total_payment"].mean()
average_session_minutes = players_df["avg_session_minutes"].mean()

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
kpi_col1.metric("总玩家数", f"{total_players:,}")
kpi_col2.metric("付费率", f"{payer_rate:.1%}")
kpi_col3.metric("平均累计付费", f"¥{average_total_payment:,.2f}")
kpi_col4.metric("平均单次时长", f"{average_session_minutes:,.1f}")
block_spacer()


def make_bar_chart(dataframe, x, y, tick_format=None, text_template=None, height=300):
    """Create consistent bar charts for the segment page."""
    fig = px.bar(dataframe, x=x, y=y, text_auto=False)
    fig.update_layout(xaxis_title="", yaxis_title="", height=height)
    if tick_format:
        fig.update_yaxes(tickformat=tick_format)
    if text_template:
        fig.update_traces(texttemplate=text_template)
    elif tick_format == ".1%":
        fig.update_traces(texttemplate="%{y:.1%}")
    else:
        fig.update_traces(texttemplate="%{y:,.0f}")
    fig.update_traces(textposition="outside", cliponaxis=False)
    if y == "payer_rate" or y == "average_churn_risk":
        apply_axis_format(fig, "y", "percent")
    elif y == "average_total_payment":
        apply_axis_format(fig, "y", "currency")
    elif y == "total_players":
        apply_axis_format(fig, "y", "count")
    elif y == "average_session_minutes":
        apply_axis_format(fig, "y", "minutes")
    return style_figure(fig)


top_chart_col1, top_chart_col2 = st.columns(2)

with top_chart_col1:
    player_count_card = section_card("玩家数")
    render_plotly_chart(
        player_count_card,
        make_bar_chart(
            segment_summary,
            "segment_label",
            "total_players",
            text_template="%{y:,.0f}",
        ),
    )

with top_chart_col2:
    payer_card = section_card("付费率")
    render_plotly_chart(
        payer_card,
        make_bar_chart(
            segment_summary,
            "segment_label",
            "payer_rate",
            ".1%",
        ),
    )

block_spacer("sm")
bottom_chart_col1, bottom_chart_col2 = st.columns(2)

with bottom_chart_col1:
    payment_card = section_card("累计付费")
    render_plotly_chart(
        payment_card,
        make_bar_chart(
            segment_summary,
            "segment_label",
            "average_total_payment",
            text_template="¥%{y:,.2f}",
        ),
    )

with bottom_chart_col2:
    session_card = section_card("活跃时长")
    render_plotly_chart(
        session_card,
        make_bar_chart(
            segment_summary,
            "segment_label",
            "average_session_minutes",
            text_template="%{y:.1f} 分钟",
        ),
    )

block_spacer("sm")
churn_card = section_card("流失风险")
render_plotly_chart(
    churn_card,
    make_bar_chart(
        segment_summary,
        "segment_label",
        "average_churn_risk",
        ".1%",
        height=320,
    ),
)

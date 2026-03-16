import pandas as pd
import streamlit as st

from src.data_loader import load_event_templates_data
from src.display_labels import EVENT_ORDER, SEGMENT_ORDER, get_event_label, get_segment_label
from src.ui import (
    apply_dashboard_theme,
    block_spacer,
    configure_page,
    filter_card,
    render_page_header,
    section_card,
)

GOAL_OPTIONS = ["活跃", "留存", "付费"]


configure_page("活动配置")
apply_dashboard_theme()


@st.cache_data
def load_event_templates():
    """Load synthetic event template data for the planning page."""
    return load_event_templates_data()


try:
    event_templates_df = load_event_templates()
except (FileNotFoundError, ValueError) as exc:
    st.error(f"活动模板数据不可用：{exc}")
    st.stop()

if event_templates_df.empty:
    st.warning("当前暂无可用的活动模板数据。")
    st.stop()

default_event = event_templates_df.iloc[0]

# Build a simple planning page for a fictional live-ops workflow.
render_page_header("活动配置", "用于模拟不同活动方案的目标圈层、奖励强度与核心目标设置。")

config_card = filter_card("活动配置")
col1, col2 = config_card.columns([1, 1])

with col1:
    event_options = [
        event_key for event_key in EVENT_ORDER if event_key in event_templates_df["event_name"].tolist()
    ]
    if not event_options:
        st.warning("当前暂无可选活动类型。")
        st.stop()

    selected_event = st.selectbox(
        "活动类型",
        event_options,
        index=0,
        format_func=get_event_label,
    )
    segment_options = SEGMENT_ORDER.copy()
    default_segment = default_event["target_segment"]
    default_index = segment_options.index(default_segment) if default_segment in segment_options else 0
    selected_target_segment = st.selectbox(
        "目标圈层",
        segment_options,
        index=default_index,
        format_func=get_segment_label,
    )
    reward_intensity = st.slider("奖励强度", min_value=1, max_value=5, value=3)

with col2:
    event_duration = st.slider("活动持续天数", min_value=3, max_value=14, value=7)
    target_goal = st.radio("核心目标指标", GOAL_OPTIONS, horizontal=True)
    generate_clicked = st.button("生成模拟方案", use_container_width=True)


selected_template = event_templates_df.loc[
    event_templates_df["event_name"] == selected_event
]
if selected_template.empty:
    st.warning("当前活动缺少对应的模板数据。")
    st.stop()
selected_template = selected_template.iloc[0]

if generate_clicked:
    st.success("方案已更新。")

summary_df = pd.DataFrame(
    {
        "项目": ["活动名称", "目标圈层", "奖励强度", "活动时长", "核心目标"],
        "内容": [
            get_event_label(selected_event),
            get_segment_label(selected_target_segment),
            f"{reward_intensity} 级",
            f"{event_duration} 天",
            target_goal,
        ],
    }
)

block_spacer()
summary_card = section_card("当前方案概览")
summary_card.dataframe(summary_df, use_container_width=True, hide_index=True)

import pandas as pd
import streamlit as st

from src.data_loader import load_event_templates_data
from src.display_labels import EVENT_ORDER, SEGMENT_ORDER, get_event_label, get_segment_label
from src.ui import (
    block_spacer,
    clear_interaction_state,
    ensure_interaction_value,
    filter_card,
    goal_to_metric,
    init_page,
    primary_button,
    render_analysis_flow,
    render_context_bar,
    render_empty_state,
    render_page_header,
    render_status_note,
    render_status_row,
    section_card,
    set_active_configuration,
    set_interaction_state,
    sync_widget_state,
)

GOAL_OPTIONS = ["活跃", "留存", "付费"]
GOAL_TO_TEMPLATE_METRIC = {
    "活跃": ("expected_activity_boost", "模板预期活跃提升"),
    "留存": ("expected_retention_boost", "模板预期留存提升"),
    "付费": ("expected_conversion_boost", "模板预期付费提升"),
}
GOAL_TO_DOWNSTREAM_LABEL = {
    "活跃": "DAU提升",
    "留存": "D7留存提升",
    "付费": "付费转化提升",
}


init_page("活动配置")


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

render_page_header("活动配置", "用于模拟不同活动方案的目标圈层、奖励强度与核心目标设置。")
block_spacer("sm")
render_analysis_flow(
    "活动配置",
    caption="承接用户分层中选定的目标圈层，把活动类型、奖励强度和目标指标收敛成一个当前生效的配置对象。",
)
block_spacer("sm")

event_options = [event_key for event_key in EVENT_ORDER if event_key in event_templates_df["event_name"].tolist()]
segment_options = SEGMENT_ORDER.copy()

if not event_options:
    st.warning("当前暂无可选活动类型。")
    st.stop()

incoming_origin = st.session_state.get("filter_origin")
active_configuration = st.session_state.get("active_configuration") or st.session_state.get("active_scenario") or {}
default_template = event_templates_df.iloc[0]

default_event = active_configuration.get("event_name") or st.session_state.get("selected_event") or default_template["event_name"]
default_segment = (
    active_configuration.get("target_segment")
    or st.session_state.get("selected_segment")
    or default_template["target_segment"]
)

if st.session_state.pop("config_reset_requested", False):
    retained_segment = st.session_state.get("selected_segment") or default_segment
    clear_interaction_state(
        ["active_configuration", "active_scenario", "selected_plan", "comparison_baseline", "comparison_target"],
        source="活动配置",
    )
    st.session_state["selected_event"] = default_template["event_name"]
    st.session_state["selected_segment"] = retained_segment
    st.session_state["config_event_widget"] = default_template["event_name"]
    st.session_state["config_segment_widget"] = retained_segment
    st.session_state["config_reward_widget"] = 3
    st.session_state["config_duration_widget"] = 7
    st.session_state["config_goal_widget"] = GOAL_OPTIONS[0]
    active_configuration = {}

ensure_interaction_value("selected_event", event_options, default_event)
ensure_interaction_value("selected_segment", segment_options, default_segment)

sync_widget_state("config_event_widget", event_options, st.session_state["selected_event"])
sync_widget_state("config_segment_widget", segment_options, st.session_state["selected_segment"])
sync_widget_state("config_reward_widget", range(1, 6), active_configuration.get("reward_intensity", 3))
sync_widget_state("config_duration_widget", range(3, 15), active_configuration.get("event_duration", 7))
sync_widget_state("config_goal_widget", GOAL_OPTIONS, active_configuration.get("target_goal", GOAL_OPTIONS[0]))

if active_configuration:
    render_status_note("当前已有生效配置，本页调整会覆盖后续默认配置。")
elif incoming_origin == "用户分层":
    render_status_note("已沿用上一页圈层，调整后可直接生成方案。")
else:
    render_status_note("当前展示草稿配置，生成后会带入后续页面。")
block_spacer("sm")

config_card = filter_card("活动配置", selected=True)
col1, col2 = config_card.columns([1, 1])

with col1:
    selected_event = st.selectbox(
        "活动类型",
        event_options,
        format_func=get_event_label,
        key="config_event_widget",
    )
    selected_target_segment = st.selectbox(
        "目标圈层",
        segment_options,
        format_func=get_segment_label,
        key="config_segment_widget",
    )
    reward_intensity = st.slider(
        "奖励强度",
        min_value=1,
        max_value=5,
        key="config_reward_widget",
    )

with col2:
    event_duration = st.slider(
        "活动持续天数",
        min_value=3,
        max_value=14,
        key="config_duration_widget",
    )
    target_goal = st.radio(
        "核心目标指标",
        GOAL_OPTIONS,
        horizontal=True,
        key="config_goal_widget",
    )
    generate_clicked = primary_button("生成模拟方案", use_container_width=True)
    st.caption("仅恢复活动与参数默认值，保留当前圈层上下文")
    if st.button("恢复默认配置", key="reset_config_draft", use_container_width=True):
        st.session_state["config_reset_requested"] = True
        st.rerun()

selected_template = event_templates_df.loc[event_templates_df["event_name"] == selected_event]
if selected_template.empty:
    st.warning("当前活动缺少对应的模板数据。")
    st.stop()
selected_template = selected_template.iloc[0]

focus_metric = goal_to_metric(target_goal)
scenario_sentence = (
    f"聚焦“{get_segment_label(selected_target_segment)}”，目标“{target_goal}”，"
    f"活动“{get_event_label(selected_event)}”，奖励 {reward_intensity} 级，持续 {event_duration} 天。"
)
set_interaction_state(
    source="活动配置",
    selected_event=selected_event,
    selected_segment=selected_target_segment,
    selected_metric_focus=target_goal,
    selected_metric=focus_metric,
)

draft_items = [
    ("活动名称", get_event_label(selected_event)),
    ("目标圈层", get_segment_label(selected_target_segment)),
    ("奖励强度", f"{reward_intensity} 级"),
    ("活动时长", f"{event_duration} 天"),
    ("核心目标", target_goal),
]

render_context_bar(
    "当前配置",
    draft_items,
    caption=(
        f"{scenario_sentence}"
        + (
            f" 当前圈层承接自{incoming_origin}。"
            if incoming_origin == "用户分层"
            else ""
        )
    ),
    emphasis="草稿",
)

block_spacer("sm")
status_card = section_card(
    "配置状态",
    caption=f"当前优先指标：{GOAL_TO_DOWNSTREAM_LABEL[target_goal]}",
    selected=True,
)
with status_card:
    render_context_bar(
        "配置摘要",
        [
            ("目标圈层", get_segment_label(selected_target_segment)),
            ("活动类型", get_event_label(selected_event)),
            ("核心目标", target_goal),
        ],
        caption=scenario_sentence,
        emphasis="草稿中",
        compact=True,
    )
render_status_row(f"当前优先指标：{GOAL_TO_DOWNSTREAM_LABEL[target_goal]}。")

if generate_clicked:
    set_active_configuration(
        {
            "event_name": selected_event,
            "target_segment": selected_target_segment,
            "reward_intensity": reward_intensity,
            "event_duration": event_duration,
            "target_goal": target_goal,
            "metric_focus": target_goal,
            "focus_metric": focus_metric,
        },
        source="活动配置",
    )
    set_interaction_state(
        source="活动配置",
        selected_plan=None,
        comparison_baseline=None,
        comparison_target=None,
    )
    st.success("方案已更新，当前配置已设为生效场景。")

block_spacer()
indicator_cols = st.columns(3)

for column, goal_name in zip(indicator_cols, GOAL_OPTIONS):
    metric_column, indicator_label = GOAL_TO_TEMPLATE_METRIC[goal_name]
    with column:
        indicator_card = section_card(
            goal_name,
            caption=indicator_label,
            selected=target_goal == goal_name,
        )
        indicator_card.metric(
            indicator_label,
            f"{selected_template[metric_column]:.1%}",
            delta="当前优先关注" if target_goal == goal_name else None,
        )

block_spacer()
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

summary_card = section_card(
    "当前方案概览",
    caption="上方调整会即时回写，便于确认配置是否成型。",
    selected=True,
)
summary_card.dataframe(summary_df, use_container_width=True, hide_index=True)

if st.session_state.get("active_scenario"):
    active = st.session_state.get("active_configuration") or st.session_state["active_scenario"]
    block_spacer("sm")
    active_card = section_card(
        "当前生效场景",
        caption="生成后，这组配置会作为后续页面的默认上下文。",
        selected=True,
    )
    with active_card:
        render_context_bar(
            "已生效配置",
            [
                ("活动名称", get_event_label(active["event_name"])),
                ("目标圈层", get_segment_label(active["target_segment"])),
                ("奖励强度", f"{active['reward_intensity']} 级"),
                ("活动时长", f"{active['event_duration']} 天"),
                ("核心目标", active["target_goal"]),
            ],
            caption=(
                f"当前生效配置会带入方案对照与活动复盘。"
                f" 当前优先指标：{GOAL_TO_DOWNSTREAM_LABEL[active['target_goal']]}。"
            ),
            emphasis="已生效",
            compact=True,
        )
else:
    block_spacer("sm")
    render_empty_state(
        "尚未生成模拟方案",
        "当前页面仅展示草稿配置，后续页面会优先读取已生效配置。",
        hint="确认参数后点击“生成模拟方案”。",
    )

import streamlit as st

from src.ui import (
    block_spacer,
    feature_card,
    init_page,
    note_card,
    render_page_header,
)


init_page("《潜水员戴夫》活动运营决策模拟器")
render_page_header(
    "《潜水员戴夫》活动运营决策模拟器",
    "基于《潜水员戴夫》玩法循环的活动运营模拟工具。",
)

block_spacer("sm")
feature_col1, feature_col2, feature_col3, feature_col4 = st.columns(4)

with feature_col1:
    feature_card(
        "用户分层",
        "先确定最值得经营的目标圈层",
        "pages/1_用户分层.py",
    )

with feature_col2:
    feature_card(
        "活动配置",
        "围绕目标圈层生成当前活动方案",
        "pages/2_活动配置.py",
    )

with feature_col3:
    feature_card(
        "方案对照",
        "比较基准方案与当前关注方案",
        "pages/3_方案对照.py",
    )

with feature_col4:
    feature_card(
        "活动复盘",
        "沿用同一上下文完成结果解读",
        "pages/4_活动复盘.py",
    )

block_spacer()
note_card("建议按 用户分层 -> 活动配置 -> 方案对照 -> 活动复盘 的顺序体验。所有数据均为合成数据，仅用于演示。")

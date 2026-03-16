import streamlit as st

from src.ui import (
    apply_dashboard_theme,
    block_spacer,
    configure_page,
    feature_card,
    note_card,
    render_page_header,
)


configure_page("《潜水员戴夫》活动运营决策模拟器")
apply_dashboard_theme()
render_page_header(
    "《潜水员戴夫》活动运营决策模拟器",
    "基于《潜水员戴夫》玩法循环的活动运营模拟工具。",
)

block_spacer("sm")
feature_col1, feature_col2, feature_col3 = st.columns(3)

with feature_col1:
    feature_card(
        "用户分层",
        "识别促活、留存与召回重点人群",
        "pages/1_用户分层.py",
    )

with feature_col2:
    feature_card(
        "方案对照",
        "比较不同活动方案在目标分层中的指标表现",
        "pages/3_方案对照.py",
    )

with feature_col3:
    feature_card(
        "活动复盘",
        "根据结果输出复盘结论与优化建议",
        "pages/4_活动复盘.py",
    )

block_spacer()
note_card("所有数据均为基于业务假设生成的合成数据，仅用于演示。")

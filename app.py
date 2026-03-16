import streamlit as st 

from src.ui import apply_dashboard_theme, configure_page 

configure_page("《潜水员戴夫》活动运营决策模拟器") 
apply_dashboard_theme() 


page_definitions = [ 
	st.Page("pages/0_首页.py", title="首页", default=True),
	st.Page("pages/1_用户分层.py", title="用户分层"), 
	st.Page("pages/2_活动配置.py", title="活动配置"), 
	st.Page("pages/3_方案对照.py", title="方案对照"), 
	st.Page("pages/4_活动复盘.py", title="活动复盘"), 
] 
	
pg = st.navigation(page_definitions, position="sidebar") 
pg.run()
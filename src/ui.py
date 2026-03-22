from __future__ import annotations

from html import escape

import streamlit as st
from streamlit.components.v1 import html as component_html


_PAGE_CONFIGURED = False


PALETTE = {
    "background": "#F7FBFB",
    "background_alt": "#F4FAF8",
    "surface": "rgba(255, 255, 255, 0.54)",
    "surface_strong": "rgba(255, 255, 255, 0.62)",
    "surface_alt": "rgba(250, 252, 252, 0.72)",
    "border": "rgba(255, 255, 255, 0.74)",
    "border_soft": "rgba(184, 198, 214, 0.24)",
    "text": "#22324D",
    "text_muted": "#5F6D86",
    "text_soft": "#7C8BA5",
    "accent": "#809BCE",
    "accent_soft": "#95B8D1",
    "accent_alt": "#B8E0D2",
    "accent_warm": "#EAC4D5",
    "accent_lilac": "#E2DBF1",
    "accent_sage": "#D6EADF",
    "highlight": "rgba(255, 255, 255, 0.90)",
    "shadow": "rgba(118, 130, 148, 0.14)",
    "shadow_deep": "rgba(118, 130, 148, 0.18)",
    "chart_grid": "rgba(190, 200, 216, 0.32)",
    "chart_axis": "#66748E",
    "chart_edge": "rgba(255, 255, 255, 0.88)",
    "hover_bg": "rgba(255, 255, 255, 0.98)",
}

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
}

INTERACTION_DEFAULTS = {
    "selected_event": None,
    "selected_segment": None,
    "selected_metric_focus": None,
    "selected_metric": None,
    "selected_plan": None,
    "comparison_baseline": None,
    "comparison_target": None,
    "selected_review_focus": None,
    "active_configuration": None,
    "active_scenario": None,
    "filter_origin": None,
    "filter_source": None,
}

GOAL_TO_METRIC = {
    "活跃": "dau_uplift",
    "留存": "d7_retention_uplift",
    "付费": "payment_conversion_uplift",
    "促活": "dau_uplift",
    "拉收": "payment_conversion_uplift",
    "综合表现": "d7_retention_uplift",
}

METRIC_TO_REVIEW_FOCUS = {
    "participation_rate": "活跃",
    "dau_uplift": "活跃",
    "total_players": "活跃",
    "average_session_minutes": "活跃",
    "payer_rate": "付费",
    "average_total_payment": "付费",
    "payment_conversion_uplift": "付费",
    "arppu_uplift": "付费",
    "d1_retention_uplift": "留存",
    "d7_retention_uplift": "留存",
    "average_churn_risk": "留存",
    "reward_cost": "成本",
    "inflation_risk": "成本",
}

def init_interaction_state() -> None:
    """Ensure shared interaction state exists before any page reads it."""
    for key, default_value in INTERACTION_DEFAULTS.items():
        st.session_state.setdefault(key, default_value)


def pick_valid_option(options, *candidates):
    """Return the first candidate that exists in options, falling back safely."""
    options = list(options)
    for candidate in candidates:
        if candidate in options:
            return candidate
    return options[0] if options else None


def ensure_interaction_value(state_key: str, options, *candidates):
    """Keep a shared state value aligned with the options available on the page."""
    init_interaction_state()
    resolved = pick_valid_option(options, st.session_state.get(state_key), *candidates)
    st.session_state[state_key] = resolved
    return resolved


def sync_widget_state(widget_key: str, options, default_value, *, pending_key: str | None = None):
    """Sync a widget key from business state before the widget is created."""
    init_interaction_state()
    option_list = list(options)
    pending_key = pending_key or f"pending_{widget_key}"
    candidate = pick_valid_option(
        option_list,
        st.session_state.pop(pending_key, None),
        st.session_state.get(widget_key),
        default_value,
    )
    st.session_state[widget_key] = candidate
    return candidate


def set_interaction_state(source: str | None = None, **values) -> None:
    """Persist meaningful analytical context across pages."""
    init_interaction_state()
    for key, value in values.items():
        if key in INTERACTION_DEFAULTS:
            st.session_state[key] = value
            if key == "active_configuration":
                st.session_state["active_scenario"] = value
            elif key == "active_scenario":
                st.session_state["active_configuration"] = value
            elif key == "comparison_target":
                st.session_state["selected_plan"] = value
    if source:
        st.session_state["filter_origin"] = source
        st.session_state["filter_source"] = source


def clear_interaction_state(keys: list[str] | tuple[str, ...] | None = None, *, source: str = "reset") -> None:
    """Clear selected interaction keys while keeping the app in a valid state."""
    init_interaction_state()
    reset_keys = keys or tuple(INTERACTION_DEFAULTS.keys())
    for key in reset_keys:
        if key in INTERACTION_DEFAULTS:
            st.session_state[key] = INTERACTION_DEFAULTS[key]
            if key == "active_configuration":
                st.session_state["active_scenario"] = INTERACTION_DEFAULTS["active_scenario"]
            elif key == "active_scenario":
                st.session_state["active_configuration"] = INTERACTION_DEFAULTS["active_configuration"]
            elif key == "comparison_target":
                st.session_state["selected_plan"] = INTERACTION_DEFAULTS["selected_plan"]
    st.session_state["filter_origin"] = source
    st.session_state["filter_source"] = source


def goal_to_metric(goal: str | None) -> str | None:
    """Map a business goal to the KPI surfaced on comparison/review pages."""
    return GOAL_TO_METRIC.get(goal)


def metric_to_review_focus(metric_key: str | None) -> str | None:
    """Map a metric key to the review dimension it most strongly represents."""
    return METRIC_TO_REVIEW_FOCUS.get(metric_key)


def normalize_focus_name(focus_name: str | None) -> str | None:
    """Normalize page-level analytical focus labels into a shared vocabulary."""
    focus_aliases = {
        "促活": "活跃",
        "拉收": "付费",
        "综合": "综合表现",
    }
    return focus_aliases.get(focus_name, focus_name)


def set_active_configuration(configuration: dict, *, source: str = "活动配置") -> None:
    """Persist the active configuration object and sync the cross-page defaults."""
    init_interaction_state()
    configuration_copy = dict(configuration)
    focus_name = normalize_focus_name(configuration_copy.get("metric_focus") or configuration_copy.get("target_goal"))
    focus_metric = configuration_copy.get("focus_metric") or goal_to_metric(configuration_copy.get("target_goal"))
    configuration_copy["metric_focus"] = focus_name
    configuration_copy["focus_metric"] = focus_metric
    set_interaction_state(
        source=source,
        active_configuration=configuration_copy,
        active_scenario=configuration_copy,
        selected_event=configuration_copy.get("event_name"),
        selected_segment=configuration_copy.get("target_segment"),
        selected_metric_focus=focus_name,
        selected_metric=focus_metric,
        selected_review_focus=metric_to_review_focus(focus_metric),
    )


def set_active_scenario(scenario: dict, *, source: str = "活动配置") -> None:
    """Backward-compatible wrapper for the active configuration object."""
    set_active_configuration(scenario, source=source)


def ensure_comparison_pair(
    options,
    *,
    preferred_baseline=None,
    preferred_target=None,
):
    """Keep baseline and target valid while avoiding an invalid self-comparison."""
    option_list = list(options)
    if not option_list:
        set_interaction_state(comparison_baseline=None, comparison_target=None, selected_plan=None)
        return None, None

    baseline = pick_valid_option(
        option_list,
        st.session_state.get("comparison_baseline"),
        preferred_baseline,
        option_list[0],
    )
    target_candidates = [
        st.session_state.get("comparison_target"),
        st.session_state.get("selected_plan"),
        preferred_target,
    ]
    target = None
    for candidate in target_candidates:
        if candidate in option_list and candidate != baseline:
            target = candidate
            break
    if target is None:
        target = next((option for option in option_list if option != baseline), baseline)
    set_interaction_state(comparison_baseline=baseline, comparison_target=target, selected_plan=target)
    return baseline, target


def render_analysis_flow(current_step: str, *, caption: str | None = None) -> None:
    """Render a compact journey strip so the analytical path stays visible."""
    steps = ["用户分层", "活动配置", "方案对照", "活动复盘"]
    step_html = []
    for step in steps:
        classes = ["analysis-step"]
        if step == current_step:
            classes.append("is-current")
        elif steps.index(step) < steps.index(current_step):
            classes.append("is-complete")
        step_html.append(f'<span class="{" ".join(classes)}">{escape(step)}</span>')

    caption_html = (
        f'<p class="analysis-flow-caption">{escape(caption)}</p>'
        if caption
        else ""
    )
    guide_html = '<p class="analysis-flow-guide">先看圈层 -> 再配活动 -> 再做对照 -> 最后复盘</p>'
    html = (
        '<div class="analysis-flow">'
        f'<div class="analysis-flow-steps">{"".join(step_html)}</div>'
        f"{guide_html}"
        f"{caption_html}"
        "</div>"
    )
    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def render_context_bar(
    title: str,
    items: list[tuple[str, str]],
    *,
    caption: str | None = None,
    emphasis: str | None = None,
    compact: bool = False,
) -> None:
    """Render a compact shared context block for active filters or scenarios."""
    caption_html = (
        f'<p class="context-bar-caption">{escape(caption)}</p>'
        if caption
        else ""
    )
    emphasis_html = (
        f'<span class="context-bar-emphasis">{escape(emphasis)}</span>'
        if emphasis
        else ""
    )
    item_html = "".join(
        (
            '<div class="context-chip">'
            f'<span class="context-chip-label">{escape(label)}</span>'
            f'<span class="context-chip-value">{escape(value)}</span>'
            "</div>"
        )
        for label, value in items
    )
    classes = "context-bar is-compact" if compact else "context-bar"
    html = (
        f'<div class="{classes}">'
        '<div class="context-bar-head">'
        f'<p class="context-bar-title">{escape(title)}</p>'
        f"{emphasis_html}"
        "</div>"
        f"{caption_html}"
        f'<div class="context-chip-grid">{item_html}</div>'
        "</div>"
    )
    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, message: str, *, hint: str | None = None) -> None:
    """Render a graceful empty or fallback state inside a styled container."""
    container = st.container(border=True)
    hint_html = (
        f'<p class="empty-state-hint">{escape(hint)}</p>'
        if hint
        else ""
    )
    html = (
        '<div class="empty-state">'
        f'<p class="empty-state-title">{escape(title)}</p>'
        f'<p class="empty-state-message">{escape(message)}</p>'
        f"{hint_html}"
        "</div>"
    )
    container.markdown(
        html,
        unsafe_allow_html=True,
    )


def configure_page(page_title: str) -> None:
    """Apply the shared Streamlit page configuration."""
    global _PAGE_CONFIGURED
    if _PAGE_CONFIGURED:
        return
    st.set_page_config(
        page_title=page_title,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _PAGE_CONFIGURED = True


def init_page(page_title: str) -> None:
    """Apply the shared page bootstrap used by every app entrypoint."""
    configure_page(page_title)
    init_interaction_state()
    apply_dashboard_theme()


def _apply_intro_shine() -> None:
    """Play a one-shot intro sheen on premium CTAs after the DOM is ready."""
    component_html(
        """
        <div style="display:none"></div>
        <script>
        (() => {
          const parentDoc = window.parent && window.parent.document;
          if (!parentDoc) return;

          const selectors = [
            '.stButton > button[kind="primary"]',
            '[data-testid="stPageLink"] a',
          ];

          let attempts = 0;
          const maxAttempts = 24;

          const animateButtons = () => {
            const targets = parentDoc.querySelectorAll(selectors.join(','));

            targets.forEach((element, index) => {
              if (element.dataset.pearlIntroShine === "done") {
                return;
              }

              element.dataset.pearlIntroShine = "done";
              window.setTimeout(() => {
                element.classList.add("intro-shine");
                window.setTimeout(() => {
                  element.classList.remove("intro-shine");
                }, 1550);
              }, 120 + index * 110);
            });

            attempts += 1;
            if (!targets.length && attempts < maxAttempts) {
              window.setTimeout(animateButtons, 120);
            }
          };

          animateButtons();

          const focusClass = "panel-focused";
          const clearFocus = () => {
            parentDoc.querySelectorAll("." + focusClass).forEach((element) => {
              element.classList.remove(focusClass);
            });
          };

          if (!window.parent.__dashboardFocusLayerBound) {
            parentDoc.addEventListener("click", (event) => {
              const target = event.target;
              if (!target || target.nodeType !== 1) {
                return;
              }

              const metric = target.closest('div[data-testid="stMetric"]');
              if (metric) {
                clearFocus();
                metric.classList.add(focusClass);
                return;
              }

              const chart = target.closest('div[data-testid="stPlotlyChart"]');
              if (chart) {
                clearFocus();
                (chart.closest('div[data-testid="stVerticalBlockBorderWrapper"]') || chart).classList.add(focusClass);
                return;
              }

              const table = target.closest('div[data-testid="stDataFrame"], div[data-testid="stTable"]');
              if (table) {
                clearFocus();
                (table.closest('div[data-testid="stVerticalBlockBorderWrapper"]') || table).classList.add(focusClass);
                return;
              }

              if (!target.closest('.stButton > button, [data-testid="stPageLink"] a')) {
                clearFocus();
              }
            }, true);

            parentDoc.addEventListener("keydown", (event) => {
              if (event.key === "Escape") {
                clearFocus();
              }
            });

            window.parent.__dashboardFocusLayerBound = true;
          }
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def apply_dashboard_theme() -> None:
    """Inject the shared light liquid-glass dashboard theme on every render."""
    st.markdown(
        f"""
        <style>
        :root {{
            color-scheme: light;
            --bg-main: {PALETTE["background"]};
            --bg-main-alt: {PALETTE["background_alt"]};
            --glass-surface: {PALETTE["surface"]};
            --glass-surface-strong: {PALETTE["surface_strong"]};
            --glass-surface-alt: {PALETTE["surface_alt"]};
            --glass-border: {PALETTE["border"]};
            --glass-outline: {PALETTE["border_soft"]};
            --glass-edge: rgba(255, 255, 255, 0.88);
            --glass-edge-soft: rgba(255, 255, 255, 0.56);
            --text-main: {PALETTE["text"]};
            --text-muted: {PALETTE["text_muted"]};
            --text-soft: {PALETTE["text_soft"]};
            --accent: {PALETTE["accent"]};
            --accent-soft: {PALETTE["accent_soft"]};
            --accent-alt: {PALETTE["accent_alt"]};
            --accent-warm: {PALETTE["accent_warm"]};
            --accent-lilac: {PALETTE["accent_lilac"]};
            --accent-sage: {PALETTE["accent_sage"]};
            --chart-grid: {PALETTE["chart_grid"]};
            --chart-axis: {PALETTE["chart_axis"]};
            --shadow-soft: 0 18px 32px rgba(118, 130, 148, 0.10), 0 6px 14px rgba(118, 130, 148, 0.05);
            --shadow-card: 0 24px 42px rgba(118, 130, 148, 0.12), 0 8px 18px rgba(118, 130, 148, 0.06);
            --shadow-feature: 0 30px 54px rgba(118, 130, 148, 0.14), 0 12px 22px rgba(118, 130, 148, 0.07);
            --shadow-raised: 0 20px 34px rgba(118, 130, 148, 0.11), 0 7px 16px rgba(118, 130, 148, 0.05);
            --glass-inset: inset 0 1px 0 rgba(255, 255, 255, 0.94), inset 0 -1px 0 rgba(214, 224, 236, 0.26), inset 0 0 0 1px rgba(184, 198, 214, 0.18);
            --glass-top-sheen: linear-gradient(180deg, rgba(255, 255, 255, 0.48) 0%, rgba(255, 255, 255, 0.18) 16%, rgba(255, 255, 255, 0) 40%);
            --glass-top-orb: radial-gradient(circle at 16% 10%, rgba(255, 255, 255, 0.72) 0%, rgba(255, 255, 255, 0.28) 20%, rgba(255, 255, 255, 0) 44%);
            --glass-bottom-bloom: radial-gradient(110% 84% at 82% 100%, rgba(232, 240, 245, 0.14) 0%, rgba(232, 240, 245, 0) 46%), radial-gradient(54% 48% at 18% 100%, rgba(248, 230, 222, 0.06) 0%, rgba(248, 230, 222, 0) 60%);
            --button-shadow: 0 12px 22px rgba(118, 130, 148, 0.10), 0 4px 10px rgba(118, 130, 148, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.94), inset 0 -1px 0 rgba(214, 224, 236, 0.24);
            --button-shadow-hover: 0 16px 28px rgba(118, 130, 148, 0.12), 0 6px 14px rgba(118, 130, 148, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.96), inset 0 -1px 0 rgba(214, 224, 236, 0.28);
            --button-shadow-primary: 0 18px 30px rgba(118, 130, 148, 0.14), 0 6px 16px rgba(118, 130, 148, 0.07), inset 0 1px 0 rgba(255, 255, 255, 0.99), inset 0 -10px 14px rgba(232, 236, 243, 0.74), inset 0 0 0 1px rgba(214, 221, 233, 0.34);
            --button-shadow-primary-hover: 0 22px 34px rgba(118, 130, 148, 0.16), 0 10px 20px rgba(118, 130, 148, 0.08), inset 0 1px 0 rgba(255, 255, 255, 1), inset 0 -12px 18px rgba(238, 242, 248, 0.80), inset 0 0 0 1px rgba(220, 225, 235, 0.40);
            --button-shadow-primary-pressed: inset 0 4px 10px rgba(214, 221, 233, 0.58), inset 0 14px 18px rgba(255, 255, 255, 0.30), 0 6px 12px rgba(118, 130, 148, 0.08);
            --ambient-honeydew: rgba(214, 234, 223, 0.38);
            --ambient-aqua: rgba(184, 224, 210, 0.32);
            --ambient-wisteria: rgba(128, 155, 206, 0.14);
            --ambient-petal: rgba(234, 196, 213, 0.10);
        }}

        @keyframes pearl-intro-shine {{
            0% {{
                background-position: 160% 0, 0 0, 0 0, 0 0;
            }}
            100% {{
                background-position: -70% 0, 0 0, 0 0, 0 0;
            }}
        }}

        @keyframes glass-breathe {{
            0% {{
                background-position: 0% 0%, 0% 0%;
                opacity: 0.92;
            }}
            50% {{
                background-position: 1.8% -2.4%, -1.2% 0.8%;
                opacity: 0.98;
            }}
            100% {{
                background-position: -1.2% 1.4%, 0.8% -1.4%;
                opacity: 0.94;
            }}
        }}

        html,
        body {{
            height: auto !important;
            min-height: 100%;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }}

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {{
            height: auto !important;
            min-height: 100vh !important;
            max-height: none !important;
            overflow: visible !important;
        }}

        .stApp {{
            position: relative;
            background:
                radial-gradient(1000px 420px at 10% 0%, rgba(184, 224, 210, 0.16), transparent 55%),
                radial-gradient(900px 460px at 100% 8%, rgba(234, 196, 213, 0.08), transparent 55%),
                radial-gradient(circle at 76% 24%, var(--ambient-honeydew) 0%, rgba(214, 234, 223, 0) 24%),
                radial-gradient(circle at 66% 16%, rgba(149, 184, 209, 0.10) 0%, rgba(149, 184, 209, 0) 20%),
                linear-gradient(180deg, #FBFDFC 0%, #F7FBFA 42%, #F3F8F6 100%);
            background-attachment: scroll;
            color: var(--text-main);
        }}

        [data-testid="stAppViewContainer"] {{
            position: relative;
            background: transparent;
        }}

        .stApp::before,
        .stApp::after,
        [data-testid="stAppViewContainer"]::before,
        [data-testid="stAppViewContainer"]::after {{
            content: none !important;
            display: none !important;
        }}

        [data-testid="stHeader"],
        [data-testid="stDecoration"] {{
            background: transparent;
        }}

        [data-testid="stAppViewContainer"] > section,
        [data-testid="stMain"],
        [data-testid="stSidebar"],
        [data-testid="stHeader"] {{
            position: relative;
            z-index: 1;
            overflow: visible;
        }}

        #MainMenu,
        [data-testid="stToolbar"],
        [data-testid="stToolbarActions"],
        [data-testid="stStatusWidget"] {{
            display: none !important;
        }}

        footer {{
            visibility: hidden;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.66) 0%, rgba(251, 252, 253, 0.78) 100%);
            border-right: 1px solid var(--glass-border);
            box-shadow: inset -1px 0 0 rgba(184, 198, 214, 0.16), 18px 0 32px rgba(118, 130, 148, 0.04);
            backdrop-filter: blur(10px) saturate(1.02);
        }}

        [data-testid="stSidebar"] > div {{
            background: transparent;
        }}

        [data-testid="stSidebarUserContent"] {{
            padding-top: 0.2rem;
        }}

        [data-testid="stSidebar"] * {{
            color: var(--text-main);
        }}

        [data-testid="stSidebarNav"] {{
            margin-top: 0.35rem;
            padding: 0.46rem;
            border: 1px solid var(--glass-border);
            border-radius: 1.35rem;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.56) 0%, rgba(250, 252, 253, 0.52) 100%);
            box-shadow: var(--shadow-soft), var(--glass-inset);
            backdrop-filter: blur(8px) saturate(1.02);
        }}

        [data-testid="stSidebarNav"] ul {{
            gap: 0.28rem;
        }}

        [data-testid="stSidebarNav"] a {{
            margin: 0;
            padding: 0.64rem 0.78rem;
            border-radius: 1rem;
            border: 1px solid rgba(255, 255, 255, 0);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.30) 0%, rgba(255, 255, 255, 0.12) 100%);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.54);
            color: var(--text-muted);
            transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
        }}

        [data-testid="stSidebarNav"] a:hover {{
            color: var(--text-main);
            border-color: rgba(255, 255, 255, 0.64);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.62) 0%, rgba(249, 251, 253, 0.50) 100%);
            box-shadow: 0 12px 20px rgba(118, 130, 148, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.84);
            transform: translateY(-1px);
        }}

        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            color: var(--text-main);
            border-color: rgba(255, 255, 255, 0.76);
            background:
                radial-gradient(circle at 18% 16%, rgba(255, 255, 255, 0.84) 0%, rgba(255, 255, 255, 0) 36%),
                linear-gradient(145deg, rgba(255, 255, 255, 0.72) 0%, rgba(250, 252, 253, 0.60) 56%, rgba(244, 247, 251, 0.62) 100%);
            box-shadow: 0 16px 24px rgba(118, 130, 148, 0.10), inset 0 1px 0 rgba(255, 255, 255, 0.90), inset 0 -1px 0 rgba(210, 220, 234, 0.22);
        }}

        [data-testid="stSidebarNav"] a[aria-current="page"] span {{
            font-weight: 700;
            color: var(--text-main);
        }}

        [data-testid="stSidebarNav"] a:focus-visible {{
            outline: none;
            box-shadow: 0 0 0 4px rgba(184, 198, 214, 0.18), 0 12px 20px rgba(118, 130, 148, 0.08);
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 2.5rem;
        }}

        .page-header {{
            margin-bottom: 1.15rem;
            max-width: 52rem;
        }}

        .page-title {{
            margin: 0;
            font-size: 2.15rem;
            font-weight: 700;
            line-height: 1.14;
            letter-spacing: -0.03em;
            color: var(--text-main);
            text-shadow: 0 1px 0 rgba(255, 255, 255, 0.72);
        }}

        .page-subtitle {{
            margin: 0.5rem 0 0;
            font-size: 0.98rem;
            line-height: 1.65;
            color: var(--text-muted);
        }}

        .section-heading {{
            margin: 0 0 0.95rem;
            font-size: 1rem;
            font-weight: 650;
            letter-spacing: 0.01em;
            color: var(--text-main);
        }}

        .section-caption {{
            margin: -0.55rem 0 1rem;
            font-size: 0.84rem;
            line-height: 1.55;
            color: var(--text-muted);
        }}

        .feature-card {{
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            height: 100%;
            min-height: 8.25rem;
            padding-top: 0.18rem;
        }}

        .feature-card::before {{
            content: "";
            display: block;
            width: 2.75rem;
            height: 0.24rem;
            margin-bottom: 1rem;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(180, 193, 233, 0.88) 0%, rgba(229, 236, 250, 0.60) 72%, rgba(255, 255, 255, 0.24) 100%);
            box-shadow: 0 6px 12px rgba(109, 125, 167, 0.10);
        }}

        .feature-card-copy {{
            display: flex;
            flex: 1 1 auto;
            flex-direction: column;
            min-height: 5.5rem;
        }}

        .feature-card-title {{
            margin: 0;
            font-size: 1.18rem;
            font-weight: 720;
            line-height: 1.34;
            color: var(--text-main);
            text-shadow: 0 1px 0 rgba(255, 255, 255, 0.72);
        }}

        .feature-card-desc {{
            margin: 0.6rem 0 0;
            max-width: 18rem;
            min-height: 3.5rem;
            font-size: 0.92rem;
            line-height: 1.72;
            color: var(--text-muted);
        }}

        .note-card-text {{
            margin: 0;
            font-size: 0.91rem;
            line-height: 1.65;
            color: var(--text-muted);
        }}

        .status-note {{
            margin: 0;
            padding: 0.8rem 0.95rem;
            border-radius: 1rem;
            border: 1px solid var(--glass-border);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.62) 0%, rgba(245, 249, 255, 0.54) 100%);
            color: var(--text-main);
            box-shadow: var(--shadow-soft), var(--glass-inset);
            font-size: 0.9rem;
            line-height: 1.5;
        }}

        .status-row {{
            margin: 0;
            padding: 0.3rem 0 0.35rem;
            color: var(--text-muted);
            font-size: 0.85rem;
            line-height: 1.5;
        }}

        .analysis-flow {{
            margin: 0;
            padding: 0.72rem 0.9rem;
            border-radius: 1.08rem;
            border: 1px solid var(--glass-border);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.64) 0%, rgba(248, 251, 253, 0.56) 100%);
            box-shadow: var(--shadow-soft), var(--glass-inset);
        }}

        .analysis-flow-steps {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}

        .analysis-step {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.3rem 0.68rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.66);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.68) 0%, rgba(249, 251, 253, 0.54) 100%);
            color: var(--text-soft);
            font-size: 0.78rem;
            font-weight: 620;
            line-height: 1.2;
        }}

        .analysis-step.is-complete {{
            color: var(--text-muted);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.74) 0%, rgba(247, 249, 252, 0.62) 100%);
        }}

        .analysis-step.is-current {{
            color: var(--text-main);
            border-color: rgba(149, 184, 209, 0.40);
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.84) 0%, rgba(244, 249, 252, 0.68) 100%);
            box-shadow: 0 12px 20px rgba(118, 130, 148, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.94);
        }}

        .analysis-flow-caption {{
            margin: 0.48rem 0 0;
            color: var(--text-muted);
            font-size: 0.8rem;
            line-height: 1.5;
        }}

        .analysis-flow-guide {{
            margin: 0.42rem 0 0;
            color: var(--text-soft);
            font-size: 0.76rem;
            line-height: 1.45;
            letter-spacing: 0.01em;
        }}

        .context-bar {{
            margin: 0;
            padding: 0.92rem 1rem;
            border-radius: 1.18rem;
            border: 1px solid var(--glass-border);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.70) 0%, rgba(246, 249, 252, 0.60) 100%);
            box-shadow: var(--shadow-soft), var(--glass-inset);
        }}

        .context-bar-head {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.9rem;
        }}

        .context-bar-title {{
            margin: 0;
            color: var(--text-main);
            font-size: 0.9rem;
            font-weight: 680;
            line-height: 1.4;
        }}

        .context-bar-caption {{
            margin: 0.25rem 0 0;
            color: var(--text-muted);
            font-size: 0.82rem;
            line-height: 1.55;
        }}

        .context-bar-emphasis {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.24rem 0.62rem;
            border-radius: 999px;
            background: rgba(149, 184, 209, 0.14);
            color: var(--text-main);
            font-size: 0.76rem;
            font-weight: 650;
            white-space: nowrap;
        }}

        .context-chip-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.62rem;
            margin-top: 0.8rem;
        }}

        .context-chip {{
            min-width: 7.2rem;
            padding: 0.58rem 0.78rem;
            border-radius: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.76);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.74) 0%, rgba(250, 252, 253, 0.58) 100%);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.92), inset 0 -1px 0 rgba(210, 220, 234, 0.22);
        }}

        .context-chip-label {{
            display: block;
            color: var(--text-soft);
            font-size: 0.75rem;
            line-height: 1.25;
        }}

        .context-chip-value {{
            display: block;
            margin-top: 0.18rem;
            color: var(--text-main);
            font-size: 0.88rem;
            font-weight: 660;
            line-height: 1.35;
        }}

        .context-bar.is-compact {{
            padding: 0.72rem 0.82rem;
            border-radius: 1.05rem;
        }}

        .context-bar.is-compact .context-bar-title {{
            font-size: 0.84rem;
        }}

        .context-bar.is-compact .context-bar-caption {{
            font-size: 0.78rem;
            line-height: 1.5;
        }}

        .context-bar.is-compact .context-chip-grid {{
            gap: 0.46rem;
            margin-top: 0.65rem;
        }}

        .context-bar.is-compact .context-chip {{
            min-width: 6.25rem;
            padding: 0.48rem 0.62rem;
            border-radius: 0.9rem;
        }}

        .context-bar.is-compact .context-chip-label {{
            font-size: 0.72rem;
        }}

        .context-bar.is-compact .context-chip-value {{
            font-size: 0.82rem;
        }}

        .empty-state {{
            padding: 0.2rem 0.1rem 0.12rem;
        }}

        .empty-state-title {{
            margin: 0;
            color: var(--text-main);
            font-size: 0.95rem;
            font-weight: 680;
            line-height: 1.35;
        }}

        .empty-state-message {{
            margin: 0.34rem 0 0;
            color: var(--text-muted);
            font-size: 0.84rem;
            line-height: 1.6;
        }}

        .empty-state-hint {{
            margin: 0.42rem 0 0;
            color: var(--text-soft);
            font-size: 0.78rem;
            line-height: 1.55;
        }}

        .compact-list {{
            margin: 0;
            padding-left: 1rem;
            color: var(--text-main);
        }}

        .compact-list li {{
            margin: 0.28rem 0;
            line-height: 1.55;
        }}

        .block-spacer-sm,
        .block-spacer-md,
        .block-spacer-lg {{
            display: block;
            width: 100%;
            line-height: 0;
        }}

        .block-spacer-sm {{
            height: 0.45rem;
        }}

        .block-spacer-md {{
            height: 0.85rem;
        }}

        .block-spacer-lg {{
            height: 1.25rem;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            position: relative;
            overflow: hidden;
            isolation: isolate;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.62) 0%, rgba(255, 255, 255, 0.56) 44%, rgba(249, 251, 253, 0.54) 100%);
            border: 1px solid var(--glass-border);
            border-radius: 1.42rem;
            padding: 1rem 1.05rem;
            box-shadow: var(--shadow-card), var(--glass-inset);
            backdrop-filter: blur(8px) saturate(1.02);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: var(--glass-top-sheen), var(--glass-top-orb);
            background-size: 106% 106%, 104% 104%;
            opacity: 1;
            animation: glass-breathe 24s ease-in-out infinite;
            pointer-events: none;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: var(--glass-bottom-bloom);
            opacity: 0.82;
            pointer-events: none;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            position: relative;
            z-index: 2;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.filter-row-anchor) {{
            padding-top: 0.9rem;
            padding-bottom: 0.9rem;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.filter-row-anchor) [data-testid="stHorizontalBlock"] {{
            align-items: end;
            gap: 0.9rem;
        }}

        [data-testid="stHorizontalBlock"]:has(.feature-card) {{
            align-items: stretch;
        }}

        [data-testid="stHorizontalBlock"]:has(.feature-card) > [data-testid="column"] {{
            display: flex;
            align-self: stretch;
        }}

        [data-testid="column"]:has(.feature-card) > div {{
            display: flex;
            flex: 1 1 auto;
            flex-direction: column;
            height: 100%;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.feature-card) {{
            display: flex;
            flex-direction: column;
            height: 100%;
            min-height: 13.8rem;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.66) 0%, rgba(255, 255, 255, 0.60) 44%, rgba(248, 250, 252, 0.58) 100%);
            border-color: rgba(255, 255, 255, 0.78);
            box-shadow: var(--shadow-feature), inset 0 1px 0 rgba(255, 255, 255, 0.96), inset 0 -1px 0 rgba(210, 220, 234, 0.28), inset 0 0 0 1px rgba(184, 198, 214, 0.14);
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.feature-card) > div,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.feature-card) [data-testid="stVerticalBlock"] {{
            display: flex;
            flex-direction: column;
            flex: 1 1 auto;
            height: 100%;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.feature-card) [data-testid="element-container"]:has(.feature-card) {{
            display: flex;
            flex: 1 1 auto;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.feature-card) [data-testid="element-container"]:has([data-testid="stPageLink"]) {{
            display: flex;
            margin-top: auto;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.feature-card) [data-testid="stPageLink"] {{
            display: flex;
            padding-top: 1.15rem;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.feature-card)::before {{
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.54) 0%, rgba(255, 255, 255, 0.20) 18%, rgba(255, 255, 255, 0) 44%),
                radial-gradient(circle at 18% 12%, rgba(255, 255, 255, 0.80) 0%, rgba(255, 255, 255, 0.32) 22%, rgba(255, 255, 255, 0) 42%);
            opacity: 1;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.feature-card)::after {{
            background: radial-gradient(110% 86% at 82% 100%, rgba(232, 240, 245, 0.16) 0%, rgba(232, 240, 245, 0) 46%), radial-gradient(54% 48% at 18% 100%, rgba(239, 234, 247, 0.08) 0%, rgba(239, 234, 247, 0) 60%);
            opacity: 0.76;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:hover,
        div[data-testid="stVerticalBlockBorderWrapper"].panel-focused {{
            transform: translateY(-1px);
            box-shadow: 0 28px 48px rgba(118, 130, 148, 0.14), var(--glass-inset);
        }}

        div[data-testid="stVerticalBlockBorderWrapper"].panel-focused {{
            border-color: rgba(149, 184, 209, 0.42);
        }}

        .interaction-state-anchor {{
            display: block;
            width: 0;
            height: 0;
            overflow: hidden;
            line-height: 0;
            font-size: 0;
        }}

        .section-card-anchor,
        .filter-row-anchor {{
            display: block;
            width: 0;
            height: 0;
            overflow: hidden;
            line-height: 0;
            font-size: 0;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.interaction-state-anchor.state-selected) {{
            border-color: rgba(149, 184, 209, 0.48);
            box-shadow: 0 30px 52px rgba(118, 130, 148, 0.16), var(--glass-inset);
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.interaction-state-anchor.state-selected) .section-heading {{
            color: #20324A;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.interaction-state-anchor.state-selected)::after {{
            background:
                radial-gradient(110% 86% at 82% 100%, rgba(232, 240, 245, 0.18) 0%, rgba(232, 240, 245, 0) 44%),
                radial-gradient(42% 38% at 16% 12%, rgba(149, 184, 209, 0.12) 0%, rgba(149, 184, 209, 0) 54%);
            opacity: 0.92;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.interaction-state-anchor.state-muted) {{
            opacity: 0.94;
        }}

        div[data-testid="stMetric"] {{
            position: relative;
            overflow: hidden;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.60) 0%, rgba(249, 251, 253, 0.54) 100%);
            border: 1px solid var(--glass-border);
            border-radius: 1.22rem;
            padding: 0.95rem 1rem;
            box-shadow: var(--shadow-raised), var(--glass-inset);
            cursor: pointer;
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
        }}

        div[data-testid="stMetric"]::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: var(--glass-top-sheen), radial-gradient(circle at 18% 12%, rgba(255, 255, 255, 0.70) 0%, rgba(255, 255, 255, 0) 30%);
            background-size: 106% 106%, 104% 104%;
            animation: glass-breathe 20s ease-in-out infinite;
            pointer-events: none;
        }}

        div[data-testid="stMetric"]::after {{
            content: "";
            position: absolute;
            inset: 0;
            background: radial-gradient(110% 82% at 84% 100%, rgba(232, 240, 245, 0.10) 0%, rgba(232, 240, 245, 0) 48%);
            pointer-events: none;
        }}

        div[data-testid="stMetric"] > div {{
            position: relative;
            z-index: 1;
        }}

        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] {{
            color: var(--text-muted);
            font-size: 0.8rem;
            font-weight: 600;
            letter-spacing: 0.01em;
        }}

        div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
            color: var(--text-main);
            font-size: 1.48rem;
            font-weight: 720;
            line-height: 1.1;
        }}

        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
            color: var(--accent);
            font-weight: 650;
        }}

        div[data-testid="stMetric"]:hover,
        div[data-testid="stMetric"].panel-focused {{
            transform: translateY(-2px);
            border-color: rgba(149, 184, 209, 0.34);
            box-shadow: 0 24px 36px rgba(118, 130, 148, 0.14), var(--glass-inset);
        }}

        div[data-testid="stMetric"].panel-focused {{
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.64) 0%, rgba(246, 249, 253, 0.58) 100%);
        }}

        .stSelectbox label,
        .stSlider label,
        .stRadio label,
        .stButton label,
        .stTextInput label,
        .stNumberInput label {{
            color: var(--text-muted);
            font-size: 0.82rem;
            font-weight: 600;
        }}

        div[data-baseweb="select"] > div,
        .stTextInput input,
        .stNumberInput input {{
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.68) 0%, rgba(249, 251, 253, 0.56) 100%);
            border: 1px solid var(--glass-border);
            border-radius: 1rem;
            box-shadow: var(--glass-inset), 0 10px 18px rgba(118, 130, 148, 0.06);
            color: var(--text-main);
            min-height: 2.8rem;
        }}

        .stSlider [data-baseweb="slider"] {{
            padding-top: 0.1rem;
            padding-bottom: 0.2rem;
        }}

        div[data-baseweb="select"] > div:focus-within,
        .stTextInput input:focus,
        .stNumberInput input:focus {{
            border-color: rgba(255, 255, 255, 0.88) !important;
            box-shadow: 0 0 0 4px rgba(184, 198, 214, 0.16), inset 0 1px 0 rgba(255, 255, 255, 0.94), 0 10px 18px rgba(118, 130, 148, 0.08);
        }}

        div[data-baseweb="popover"],
        div[role="listbox"] {{
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.86) 0%, rgba(250, 252, 253, 0.78) 100%);
            border: 1px solid var(--glass-border);
            border-radius: 1rem;
            box-shadow: var(--shadow-soft), var(--glass-inset);
            backdrop-filter: blur(8px) saturate(1.02);
        }}

        div[role="option"] {{
            color: var(--text-main);
            border-radius: 0.8rem;
        }}

        div[role="option"]:hover {{
            background: rgba(225, 233, 245, 0.18);
        }}

        div[role="option"][aria-selected="true"] {{
            background: rgba(225, 233, 245, 0.24);
        }}

        div[role="radiogroup"] {{
            gap: 0.55rem;
        }}

        div[role="radiogroup"] label {{
            padding: 0.45rem 0.82rem;
            border-radius: 999px;
            border: 1px solid var(--glass-border);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.62) 0%, rgba(249, 251, 253, 0.50) 100%);
            box-shadow: var(--glass-inset);
            transition: border-color 0.16s ease, box-shadow 0.16s ease, background 0.16s ease, transform 0.16s ease;
        }}

        div[role="radiogroup"] label:hover {{
            border-color: rgba(255, 255, 255, 0.82);
            transform: translateY(-1px);
        }}

        div[role="radiogroup"] label:has(input:checked) {{
            border-color: rgba(255, 255, 255, 0.82);
            background: linear-gradient(160deg, rgba(255, 255, 255, 0.76) 0%, rgba(246, 249, 252, 0.66) 100%);
            box-shadow: 0 12px 20px rgba(118, 130, 148, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.92), inset 0 -1px 0 rgba(210, 220, 234, 0.24);
        }}

        div[data-baseweb="radio"] input:checked + div {{
            border-color: var(--accent) !important;
            background-color: var(--accent) !important;
            box-shadow: 0 0 0 4px rgba(184, 198, 214, 0.14);
        }}

        div[data-baseweb="radio"] div[aria-checked="true"] {{
            color: var(--accent);
        }}

        .stSlider [data-baseweb="slider"] > div > div {{
            background: linear-gradient(90deg, rgba(150, 176, 196, 0.96) 0%, rgba(184, 200, 215, 0.92) 100%);
        }}

        .stSlider [data-baseweb="slider"] [role="slider"] {{
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(246, 249, 252, 0.96) 100%);
            border: 1px solid rgba(255, 255, 255, 0.88);
            box-shadow: 0 10px 18px rgba(118, 130, 148, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.96);
        }}

        .stButton > button {{
            position: relative;
            overflow: hidden;
            isolation: isolate;
            min-height: 2.75rem;
            border: 1px solid var(--glass-border);
            border-radius: 999px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.82) 0%, rgba(248, 250, 252, 0.72) 100%);
            color: #516271;
            font-weight: 620;
            letter-spacing: 0;
            box-shadow: var(--button-shadow);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease, color 0.18s ease, filter 0.18s ease;
        }}

        .stButton > button::before {{
            content: "";
            position: absolute;
            inset: 1px;
            border-radius: inherit;
            background:
                linear-gradient(180deg, rgba(255, 255, 255, 0.44) 0%, rgba(255, 255, 255, 0.12) 22%, rgba(255, 255, 255, 0) 48%),
                radial-gradient(circle at 24% 18%, rgba(255, 255, 255, 0.88) 0%, rgba(255, 255, 255, 0.52) 26%, rgba(255, 255, 255, 0) 54%),
                linear-gradient(135deg, rgba(255, 255, 255, 0.42) 0%, rgba(244, 247, 252, 0.16) 42%, rgba(220, 229, 243, 0.10) 72%, rgba(247, 236, 244, 0.08) 100%);
            opacity: 0.9;
            pointer-events: none;
            transition: opacity 0.18s ease, background-position 0.18s ease;
        }}

        .stButton > button::after {{
            content: "";
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background: radial-gradient(90% 90% at 82% 100%, rgba(224, 232, 244, 0.18) 0%, rgba(224, 232, 244, 0) 48%), radial-gradient(42% 52% at 18% 100%, rgba(247, 236, 244, 0.12) 0%, rgba(247, 236, 244, 0) 60%);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.92), inset 0 -1px 0 rgba(210, 220, 234, 0.26);
            opacity: 0.64;
            pointer-events: none;
            transition: opacity 0.18s ease, box-shadow 0.18s ease;
        }}

        .stButton > button > div,
        .stButton > button p,
        .stButton > button span {{
            position: relative;
            z-index: 1;
            color: inherit;
        }}

        .stButton > button:hover {{
            color: var(--text-main);
            border-color: rgba(255, 255, 255, 0.84);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.90) 0%, rgba(249, 251, 253, 0.80) 100%);
            box-shadow: var(--button-shadow-hover);
            transform: translateY(-1px);
            filter: saturate(1.03) brightness(1.015);
        }}

        .stButton > button:active {{
            transform: translateY(1px);
            background: linear-gradient(180deg, rgba(248, 249, 251, 0.88) 0%, rgba(242, 245, 249, 0.80) 100%);
            box-shadow: inset 0 3px 8px rgba(214, 224, 236, 0.38), 0 6px 12px rgba(118, 130, 148, 0.08);
        }}

        .stButton > button:focus-visible,
        .stButton > button:focus {{
            outline: none;
            box-shadow: 0 0 0 4px rgba(184, 198, 214, 0.20), var(--button-shadow-hover);
        }}

        .stButton > button[kind="primary"],
        [data-testid="stPageLink"] a {{
            position: relative;
            overflow: hidden;
            isolation: isolate;
            border: 1px solid rgba(255, 255, 255, 0.92);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.995) 0%, rgba(253, 254, 255, 0.99) 40%, rgba(246, 248, 250, 0.97) 100%);
            color: #4E5F65;
            font-weight: 700;
            box-shadow: var(--button-shadow-primary);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease, color 0.18s ease, filter 0.18s ease;
        }}

        .stButton > button[kind="primary"]::before,
        [data-testid="stPageLink"] a::before {{
            content: "";
            position: absolute;
            inset: 1px;
            border-radius: inherit;
            background:
                linear-gradient(112deg, rgba(255, 255, 255, 0) 34%, rgba(255, 255, 255, 0.86) 48%, rgba(255, 255, 255, 0) 62%),
                linear-gradient(180deg, rgba(255, 255, 255, 0.72) 0%, rgba(255, 255, 255, 0.24) 20%, rgba(255, 255, 255, 0) 50%),
                radial-gradient(circle at 22% 14%, rgba(255, 255, 255, 0.99) 0%, rgba(255, 255, 255, 0.80) 28%, rgba(255, 255, 255, 0) 60%),
                linear-gradient(132deg, rgba(224, 233, 246, 0.22) 0%, rgba(239, 234, 247, 0.18) 52%, rgba(248, 230, 222, 0.18) 100%);
            background-size: 220% 100%, 100% 100%, 100% 100%, 100% 100%;
            background-position: 160% 0, 0 0, 0 0, 0 0;
            opacity: 0.94;
            pointer-events: none;
            transition: opacity 0.18s ease, background-position 0.18s ease;
        }}

        .stButton > button[kind="primary"]::after,
        [data-testid="stPageLink"] a::after {{
            content: "";
            position: absolute;
            inset: 0;
            border-radius: inherit;
            background:
                radial-gradient(96% 92% at 82% 100%, rgba(224, 232, 244, 0.18) 0%, rgba(224, 232, 244, 0) 46%),
                radial-gradient(42% 54% at 18% 100%, rgba(248, 230, 222, 0.16) 0%, rgba(248, 230, 222, 0) 60%),
                radial-gradient(58% 48% at 54% 18%, rgba(239, 234, 247, 0.16) 0%, rgba(239, 234, 247, 0) 64%);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.98), inset 0 -1px 0 rgba(214, 221, 233, 0.40);
            opacity: 0.78;
            pointer-events: none;
            transition: opacity 0.18s ease, box-shadow 0.18s ease;
        }}

        .stButton > button[kind="primary"].intro-shine::before,
        [data-testid="stPageLink"] a.intro-shine::before {{
            animation: pearl-intro-shine 1.5s cubic-bezier(0.21, 0.82, 0.26, 1);
        }}

        .stButton > button[kind="primary"]:hover,
        [data-testid="stPageLink"] a:hover {{
            border-color: rgba(255, 255, 255, 0.96);
            background: linear-gradient(180deg, rgba(255, 255, 255, 1) 0%, rgba(254, 255, 255, 0.998) 36%, rgba(250, 251, 253, 0.994) 100%);
            box-shadow: var(--button-shadow-primary-hover);
            transform: translateY(-2px);
            filter: saturate(1.05) brightness(1.018);
        }}

        .stButton > button[kind="primary"]:hover::before,
        [data-testid="stPageLink"] a:hover::before {{
            opacity: 1;
        }}

        .stButton > button[kind="primary"]:hover::after,
        [data-testid="stPageLink"] a:hover::after {{
            opacity: 0.92;
        }}

        .stButton > button[kind="primary"]:active,
        [data-testid="stPageLink"] a:active {{
            transform: translateY(1px);
            background: linear-gradient(180deg, rgba(247, 249, 251, 0.99) 0%, rgba(241, 244, 248, 0.97) 100%);
            box-shadow: var(--button-shadow-primary-pressed);
            filter: none;
        }}

        .stButton > button[kind="primary"]:focus-visible,
        .stButton > button[kind="primary"]:focus,
        [data-testid="stPageLink"] a:focus-visible,
        [data-testid="stPageLink"] a:focus {{
            outline: none;
            box-shadow: 0 0 0 4px rgba(184, 198, 214, 0.24), var(--button-shadow-primary-hover);
        }}

        [data-testid="stPageLink"] a {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: fit-content;
            padding: 0.58rem 0.95rem;
            border-radius: 999px;
            text-decoration: none;
            font-size: 0.86rem;
            font-weight: 600;
        }}

        [data-testid="stPageLink"] a,
        [data-testid="stPageLink"] a * {{
            color: inherit;
        }}

        [data-testid="stPageLink"] a > span,
        [data-testid="stPageLink"] a > div {{
            position: relative;
            z-index: 1;
        }}

        .stDataFrame,
        div[data-testid="stDataFrame"],
        div[data-testid="stTable"] {{
            border: 1px solid var(--glass-border);
            border-radius: 1.05rem;
            overflow: hidden;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.58) 0%, rgba(249, 251, 253, 0.50) 100%);
            box-shadow: var(--shadow-soft), var(--glass-inset);
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
            --gdg-accent-color: rgba(128, 155, 206, 0.24);
            --gdg-accent-fg: {PALETTE["text"]};
            --gdg-bg-header: rgba(255, 255, 255, 0.82);
            --gdg-bg-cell: rgba(255, 255, 255, 0.12);
            --gdg-bg-cell-medium: rgba(149, 184, 209, 0.08);
            --gdg-bg-row-hover: rgba(149, 184, 209, 0.10);
            --gdg-border-color: rgba(184, 198, 214, 0.22);
            --gdg-text-dark: {PALETTE["text"]};
        }}

        div[data-testid="stDataFrame"]:hover,
        div[data-testid="stTable"]:hover,
        div[data-testid="stVerticalBlockBorderWrapper"].panel-focused div[data-testid="stDataFrame"],
        div[data-testid="stVerticalBlockBorderWrapper"].panel-focused div[data-testid="stTable"] {{
            border-color: rgba(149, 184, 209, 0.34);
            box-shadow: 0 18px 30px rgba(118, 130, 148, 0.10), var(--glass-inset);
        }}

        div[data-testid="stTable"] tbody tr {{
            transition: background-color 0.16s ease;
        }}

        div[data-testid="stTable"] tbody tr:hover td {{
            background: rgba(149, 184, 209, 0.10);
        }}

        div[data-testid="stDataFrame"] [role="row"] {{
            transition: background-color 0.16s ease;
        }}

        div[data-testid="stDataFrame"] [role="row"]:hover [role="gridcell"] {{
            background: rgba(149, 184, 209, 0.08) !important;
        }}

        div[data-testid="stAlertContainer"] > div {{
            border-radius: 1rem;
            border: 1px solid var(--glass-border);
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.64) 0%, rgba(249, 251, 253, 0.58) 100%);
            box-shadow: var(--shadow-soft), var(--glass-inset);
            backdrop-filter: blur(8px);
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid var(--glass-border);
            border-radius: 1.1rem;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.60) 0%, rgba(249, 251, 253, 0.54) 100%);
            box-shadow: var(--shadow-soft), var(--glass-inset);
            overflow: hidden;
        }}

        div[data-testid="stExpander"] summary p {{
            color: var(--text-main);
            font-weight: 650;
        }}

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li {{
            color: var(--text-main);
        }}

        .stCaption,
        [data-testid="stCaptionContainer"] {{
            color: var(--text-muted);
        }}

        .stPlotlyChart,
        div[data-testid="stPlotlyChart"] {{
            border: 1px solid var(--glass-border);
            border-radius: 1.08rem;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.58) 0%, rgba(249, 251, 253, 0.50) 100%);
            box-shadow: var(--shadow-soft), var(--glass-inset);
            overflow: hidden;
            transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, filter 0.18s ease;
        }}

        .stPlotlyChart:hover,
        div[data-testid="stPlotlyChart"]:hover,
        div[data-testid="stVerticalBlockBorderWrapper"].panel-focused div[data-testid="stPlotlyChart"] {{
            border-color: rgba(149, 184, 209, 0.34);
            box-shadow: 0 22px 34px rgba(118, 130, 148, 0.12), var(--glass-inset);
            filter: saturate(1.02);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    _apply_intro_shine()


def render_page_header(title: str, subtitle: str) -> None:
    """Render a consistent dashboard page header."""
    html = (
        '<div class="page-header">'
        f'<h1 class="page-title">{escape(title)}</h1>'
        f'<p class="page-subtitle">{escape(subtitle)}</p>'
        "</div>"
    )
    st.markdown(
        html,
        unsafe_allow_html=True,
    )


def _render_card_state_marker(container, *, selected: bool = False, muted: bool = False) -> None:
    """Attach a hidden marker so CSS can visually emphasize selected cards."""
    classes = ["interaction-state-anchor"]
    if selected:
        classes.append("state-selected")
    if muted:
        classes.append("state-muted")
    container.markdown(
        f'<span class="{" ".join(classes)}" aria-hidden="true">&#8203;</span>',
        unsafe_allow_html=True,
    )


def section_card(
    title: str | None = None,
    caption: str | None = None,
    *,
    selected: bool = False,
    muted: bool = False,
):
    """Return a bordered container styled as a dashboard section card."""
    container = st.container(border=True)
    _render_card_state_marker(container, selected=selected, muted=muted)
    container.markdown(
        '<span class="section-card-anchor" aria-hidden="true">&#8203;</span>',
        unsafe_allow_html=True,
    )
    if title:
        container.markdown(
            f'<div class="section-heading">{escape(title)}</div>',
            unsafe_allow_html=True,
        )
    if caption:
        container.markdown(
            f'<div class="section-caption">{escape(caption)}</div>',
            unsafe_allow_html=True,
        )
    return container


def filter_card(title: str = "筛选条件", *, selected: bool = False):
    """Return a compact bordered container for page filters."""
    container = st.container(border=True)
    _render_card_state_marker(container, selected=selected)
    container.markdown(
        '<span class="filter-row-anchor" aria-hidden="true">&#8203;</span>',
        unsafe_allow_html=True,
    )
    container.markdown(
        f'<div class="section-heading">{escape(title)}</div>',
        unsafe_allow_html=True,
    )
    return container


def block_spacer(size: str = "md") -> None:
    """Add shared vertical rhythm between layout blocks."""
    if size not in {"sm", "md", "lg"}:
        size = "md"
    st.markdown(
        f'<span class="block-spacer-{size}" aria-hidden="true">&#8203;</span>',
        unsafe_allow_html=True,
    )


def primary_button(label: str, **kwargs) -> bool:
    """Render a shared primary action button."""
    kwargs.setdefault("type", "primary")
    return st.button(label, **kwargs)


def feature_card(title: str, description: str, page_path: str) -> None:
    """Render a concise homepage feature card."""
    container = st.container(border=True)
    html = (
        '<div class="feature-card">'
        '<div class="feature-card-copy">'
        f'<h3 class="feature-card-title">{escape(title)}</h3>'
        f'<p class="feature-card-desc">{escape(description)}</p>'
        "</div>"
        "</div>"
    )
    container.markdown(
        html,
        unsafe_allow_html=True,
    )
    container.page_link(page_path, label="进入模块")


def note_card(message: str) -> None:
    """Render a compact note card used for product-level context."""
    container = st.container(border=True)
    container.markdown(
        f'<p class="note-card-text">{escape(message)}</p>',
        unsafe_allow_html=True,
    )


def render_status_note(message: str) -> None:
    """Render a short product-like status note."""
    st.markdown(
        f'<p class="status-note">{escape(message)}</p>',
        unsafe_allow_html=True,
    )


def render_status_row(message: str) -> None:
    """Render a lightweight inline status row."""
    st.markdown(
        f'<p class="status-row">{escape(message)}</p>',
        unsafe_allow_html=True,
    )


def render_compact_list(items: list[str]) -> None:
    """Render a tighter list for dashboard content cards."""
    list_items = "".join(f"<li>{escape(item)}</li>" for item in items)
    st.markdown(f'<ul class="compact-list">{list_items}</ul>', unsafe_allow_html=True)


def style_figure(fig, *, show_legend: bool = False):
    """Apply the shared light glass styling to Plotly figures."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": PALETTE["text"], "size": 12},
        showlegend=show_legend,
        clickmode="event+select",
        hovermode="closest",
        uirevision="interactive-theme",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "font": {"color": PALETTE["text_muted"], "size": 11},
            "bgcolor": "rgba(255,255,255,0.38)",
        },
        hoverlabel={
            "bgcolor": PALETTE["hover_bg"],
            "bordercolor": PALETTE["accent_soft"],
            "font": {"color": PALETTE["text"], "size": 12},
        },
        margin={"l": 12, "r": 12, "t": 38, "b": 12},
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=PALETTE["chart_grid"],
        zerolinecolor=PALETTE["border_soft"],
        linecolor=PALETTE["border_soft"],
        color=PALETTE["chart_axis"],
        tickfont={"size": 11},
        title_font={"size": 11, "color": PALETTE["text_muted"]},
        automargin=True,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=PALETTE["chart_grid"],
        zerolinecolor=PALETTE["border_soft"],
        linecolor=PALETTE["border_soft"],
        color=PALETTE["chart_axis"],
        tickfont={"size": 11},
        title_font={"size": 11, "color": PALETTE["text_muted"]},
        automargin=True,
    )
    for trace in fig.data:
        trace_type = getattr(trace, "type", None)
        if trace_type == "bar":
            trace.marker.line.color = PALETTE["chart_edge"]
            trace.marker.line.width = 1.1
            trace.opacity = 0.92
            trace.textfont = {"color": PALETTE["text"], "size": 11}
            trace.selected = {"marker": {"opacity": 1}}
            trace.unselected = {"marker": {"opacity": 0.38}}
            trace.hoverlabel = {
                "bgcolor": PALETTE["hover_bg"],
                "bordercolor": PALETTE["accent_soft"],
            }
        elif trace_type == "scatter":
            trace.selected = {"marker": {"opacity": 1}}
            trace.unselected = {"marker": {"opacity": 0.36}}
    return fig


def apply_axis_format(fig, axis: str, value_format: str) -> None:
    """Apply a shared axis format for count, percent, currency, or minutes."""
    if axis not in {"x", "y"}:
        return
    update_axis = fig.update_xaxes if axis == "x" else fig.update_yaxes
    if value_format == "percent":
        update_axis(tickformat=".0%")
    elif value_format == "currency":
        update_axis(tickprefix="¥", tickformat=",.0f")
    elif value_format == "count":
        update_axis(tickformat=",.0f")
    elif value_format == "minutes":
        update_axis(ticksuffix=" 分")


def render_plotly_chart(container, fig) -> None:
    """Render Plotly charts with the shared Streamlit config."""
    container.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOTLY_CONFIG,
        theme="streamlit",
    )

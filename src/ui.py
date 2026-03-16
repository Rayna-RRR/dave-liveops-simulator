from __future__ import annotations

from html import escape

import streamlit as st


_PAGE_CONFIGURED = False


PALETTE = {
    "background": "#0C0C0E",
    "surface": "#17181B",
    "surface_alt": "#1D1F23",
    "border": "#4B4438",
    "border_soft": "#363229",
    "text": "#EEE7DA",
    "text_muted": "#A79F93",
    "accent": "#B19A68",
    "accent_soft": "#C4B084",
    "accent_deep": "#8E7A54",
    "accent_alt": "#6F7A88",
}

PLOTLY_COLORWAY = [
    PALETTE["accent"],
    PALETTE["accent_alt"],
    "#8E959D",
    PALETTE["accent_deep"],
]

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
}


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


def apply_dashboard_theme() -> None:
    """Inject the shared dashboard CSS."""
    st.markdown(
        f"""
        <style>
        :root {{
            --bg-main: {PALETTE["background"]};
            --bg-surface: {PALETTE["surface"]};
            --bg-surface-alt: {PALETTE["surface_alt"]};
            --border-color: {PALETTE["border"]};
            --border-soft: {PALETTE["border_soft"]};
            --text-main: {PALETTE["text"]};
            --text-muted: {PALETTE["text_muted"]};
            --accent: {PALETTE["accent"]};
            --accent-soft: {PALETTE["accent_soft"]};
            --accent-deep: {PALETTE["accent_deep"]};
        }}

        .stApp {{
            background-color: var(--bg-main);
            color: var(--text-main);
        }}

        [data-testid="stAppViewContainer"] {{
            background: var(--bg-main);
        }}

        [data-testid="stHeader"],
        [data-testid="stDecoration"] {{
            background: transparent;
        }}

        .stAppDeployButton {{
            display: none;
        }}

        #MainMenu,
        footer {{
            visibility: hidden;
        }}

        [data-testid="stSidebar"] {{
            background-color: #121315;
            border-right: 1px solid var(--border-soft);
        }}

        [data-testid="stSidebar"] * {{
            color: var(--text-main);
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 2.25rem;
        }}

        .page-title {{
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.2;
            letter-spacing: -0.02em;
            color: var(--text-main);
        }}

        .page-header {{
            margin-bottom: 1.1rem;
        }}

        .page-subtitle {{
            margin: 0.45rem 0 0;
            font-size: 0.98rem;
            line-height: 1.6;
            color: var(--text-muted);
        }}

        .section-heading {{
            margin: 0 0 1rem;
            font-size: 1.02rem;
            font-weight: 600;
            letter-spacing: 0.01em;
            color: var(--text-main);
        }}

        .section-caption {{
            margin: -0.6rem 0 1rem;
            font-size: 0.84rem;
            color: var(--text-muted);
        }}

        .feature-card-title {{
            margin: 0;
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-main);
        }}

        .feature-card-desc {{
            margin: 0.45rem 0 0;
            font-size: 0.88rem;
            line-height: 1.6;
            color: var(--text-muted);
        }}

        .note-card-text {{
            margin: 0;
            font-size: 0.9rem;
            line-height: 1.6;
            color: var(--text-muted);
        }}

        .status-note {{
            margin: 0;
            padding: 0.7rem 0.85rem;
            border-radius: 12px;
            border: 1px solid rgba(177, 154, 104, 0.22);
            background: rgba(177, 154, 104, 0.10);
            color: var(--text-main);
            font-size: 0.9rem;
            line-height: 1.45;
        }}

        .status-row {{
            margin: 0;
            padding: 0.15rem 0 0.2rem;
            color: var(--text-muted);
            font-size: 0.84rem;
            line-height: 1.45;
        }}

        .compact-list {{
            margin: 0;
            padding-left: 1rem;
            color: var(--text-main);
        }}

        .compact-list li {{
            margin: 0.2rem 0;
            line-height: 1.45;
        }}

        .block-spacer-sm {{
            height: 0.4rem;
        }}

        .block-spacer-md {{
            height: 0.8rem;
        }}

        .block-spacer-lg {{
            height: 1.2rem;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--bg-surface);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1rem 1.05rem;
            box-shadow: none;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.filter-row-anchor) {{
            padding-top: 0.85rem;
            padding-bottom: 0.85rem;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.filter-row-anchor) [data-testid="stHorizontalBlock"] {{
            align-items: end;
            gap: 0.75rem;
        }}

        div[data-testid="stMetric"] {{
            background: var(--bg-surface-alt);
            border: 1px solid var(--border-soft);
            border-radius: 14px;
            padding: 0.85rem 0.95rem;
        }}

        div[data-testid="stMetric"] label {{
            color: var(--text-muted);
            font-size: 0.8rem;
            font-weight: 500;
        }}

        div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
            color: var(--text-main);
            font-size: 1.5rem;
            font-weight: 700;
            line-height: 1.1;
        }}

        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {{
            color: var(--accent);
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
        .stSlider [data-baseweb="slider"] {{
            background: var(--bg-surface-alt);
            border-radius: 12px;
        }}

        div[data-baseweb="select"] > div {{
            border: 1px solid var(--border-soft);
            min-height: 42px;
        }}

        div[data-baseweb="select"] > div:focus-within,
        .stTextInput input:focus,
        .stNumberInput input:focus {{
            border-color: var(--accent) !important;
            box-shadow: 0 0 0 1px rgba(177, 154, 104, 0.22);
        }}

        div[data-baseweb="popover"] {{
            background: var(--bg-surface-alt);
            border: 1px solid var(--border-soft);
        }}

        div[role="listbox"] {{
            background: var(--bg-surface-alt);
            border: 1px solid var(--border-soft);
        }}

        div[role="option"][aria-selected="true"] {{
            background: rgba(177, 154, 104, 0.16);
        }}

        div[data-baseweb="radio"] {{
            gap: 0.75rem;
        }}

        div[data-baseweb="radio"] label {{
            color: var(--text-main);
        }}

        div[data-baseweb="radio"] input:checked + div {{
            border-color: var(--accent) !important;
            background-color: var(--accent) !important;
        }}

        div[data-baseweb="radio"] div[aria-checked="true"] {{
            color: var(--accent);
        }}

        .stSlider [data-baseweb="slider"] [role="slider"] {{
            background: var(--accent);
            box-shadow: 0 0 0 4px rgba(177, 154, 104, 0.14);
        }}

        .stSlider [data-baseweb="slider"] > div > div {{
            background: var(--accent);
        }}

        .stButton > button {{
            background: var(--accent);
            color: #151412;
            border: 1px solid rgba(177, 154, 104, 0.2);
            border-radius: 10px;
            min-height: 2.6rem;
            font-weight: 700;
        }}

        .stButton > button:hover {{
            background: var(--accent-soft);
        }}

        .stButton > button:focus {{
            box-shadow: 0 0 0 2px rgba(177, 154, 104, 0.18);
            outline: none;
        }}

        [data-testid="stPageLink"] a {{
            color: var(--accent);
            text-decoration: none;
            font-size: 0.86rem;
            font-weight: 600;
        }}

        [data-testid="stPageLink"] a:hover {{
            color: var(--accent-soft);
        }}

        .stDataFrame,
        div[data-testid="stTable"] {{
            border: 1px solid var(--border-soft);
            border-radius: 12px;
            overflow: hidden;
        }}

        div[data-testid="stAlertContainer"] > div {{
            background: rgba(177, 154, 104, 0.10);
            border: 1px solid rgba(177, 154, 104, 0.22);
            color: var(--text-main);
            border-radius: 12px;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid var(--border-soft);
            border-radius: 12px;
            background: var(--bg-surface-alt);
        }}

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        .stCaption {{
            color: var(--text-main);
        }}

        .stCaption {{
            color: var(--text-muted);
        }}

        .stPlotlyChart {{
            border-radius: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, subtitle: str) -> None:
    """Render a consistent dashboard page header."""
    st.markdown(
        f"""
        <div class="page-header">
            <h1 class="page-title">{escape(title)}</h1>
            <p class="page-subtitle">{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_card(title: str | None = None, caption: str | None = None):
    """Return a bordered container styled as a dashboard section card."""
    container = st.container(border=True)
    container.markdown('<div class="section-card-anchor"></div>', unsafe_allow_html=True)
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


def filter_card(title: str = "筛选条件"):
    """Return a compact bordered container for page filters."""
    container = st.container(border=True)
    container.markdown('<div class="filter-row-anchor"></div>', unsafe_allow_html=True)
    container.markdown(
        f'<div class="section-heading">{escape(title)}</div>',
        unsafe_allow_html=True,
    )
    return container


def block_spacer(size: str = "md") -> None:
    """Add shared vertical rhythm between layout blocks."""
    if size not in {"sm", "md", "lg"}:
        size = "md"
    st.markdown(f'<div class="block-spacer-{size}"></div>', unsafe_allow_html=True)


def feature_card(title: str, description: str, page_path: str) -> None:
    """Render a concise homepage feature card."""
    container = st.container(border=True)
    container.markdown(
        f"""
        <div class="feature-card">
            <h3 class="feature-card-title">{escape(title)}</h3>
            <p class="feature-card-desc">{escape(description)}</p>
        </div>
        """,
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
    """Apply the shared dark dashboard styling to Plotly figures."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": PALETTE["text"], "size": 12},
        colorway=PLOTLY_COLORWAY,
        showlegend=show_legend,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "right",
            "x": 1,
            "font": {"color": PALETTE["text_muted"], "size": 11},
        },
        hoverlabel={
            "bgcolor": PALETTE["surface_alt"],
            "bordercolor": PALETTE["border"],
            "font": {"color": PALETTE["text"], "size": 12},
        },
        margin={"l": 12, "r": 12, "t": 40, "b": 12},
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor=PALETTE["border_soft"],
        zerolinecolor=PALETTE["border"],
        linecolor=PALETTE["border_soft"],
        color=PALETTE["text_muted"],
        tickfont={"size": 11},
        title_font={"size": 11, "color": PALETTE["text_muted"]},
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=PALETTE["border_soft"],
        zerolinecolor=PALETTE["border"],
        linecolor=PALETTE["border_soft"],
        color=PALETTE["text_muted"],
        tickfont={"size": 11},
        title_font={"size": 11, "color": PALETTE["text_muted"]},
    )
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
    container.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

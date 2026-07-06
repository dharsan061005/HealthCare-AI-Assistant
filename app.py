"""
Healthcare AI Assistant — Main Streamlit Application
Entry point: streamlit run app.py
"""

import logging
import sys
import os
from pathlib import Path

# ── Guarantee project root is on sys.path ─────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
_root_str = str(ROOT_DIR)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)
os.chdir(ROOT_DIR)

import streamlit as st

import config
from agents.router import NAV_ITEMS, DEFAULT_PAGE, get_agent_renderer
from database.database import init_db

logger = logging.getLogger(__name__)

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": f"**{config.APP_TITLE}** v{config.APP_VERSION}\n\nAI-powered healthcare assistant.",
    },
)


def _load_css() -> None:
    css_path = config.ASSETS_DIR / "styles.css"
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def _ensure_db_initialized() -> None:
    if "db_initialized" not in st.session_state:
        try:
            init_db()
            st.session_state.db_initialized = True
        except Exception as e:
            st.error(f"**Database Error:** {e}")
            logger.critical("Database init failed: %s", e)
            st.session_state.db_initialized = False


def _render_sidebar() -> str:
    # ── Session state default ─────────────────────────────────────────────────
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = DEFAULT_PAGE

    # ── Sidebar — 100% native Streamlit, zero custom HTML ────────────────────
    st.sidebar.title("🏥 Healthcare AI")
    st.sidebar.caption("Your AI-powered health assistant")
    st.sidebar.divider()

    st.sidebar.markdown("**NAVIGATION**")

    selected = st.sidebar.radio(
        label="Go to",
        options=NAV_ITEMS,
        index=NAV_ITEMS.index(st.session_state.selected_page),
        key="sidebar_nav",
        label_visibility="collapsed",
    )
    st.session_state.selected_page = selected

    st.sidebar.divider()

    st.sidebar.markdown("**SYSTEM STATUS**")
    api_ok = bool(config.GROQ_API_KEY)
    db_ok  = st.session_state.get("db_initialized", False)
    st.sidebar.markdown(
        f"{'🟢' if api_ok else '🔴'} Groq API — {'Active' if api_ok else 'Not set'}"
    )
    st.sidebar.markdown(
        f"{'🟢' if db_ok else '🔴'} Database — {'Connected' if db_ok else 'Error'}"
    )

    st.sidebar.divider()
    st.sidebar.caption(
        "⚠️ AI-generated information only. "
        "Always consult a qualified healthcare professional."
    )

    return selected


def main() -> None:
    _load_css()
    _ensure_db_initialized()
    selected_page = _render_sidebar()

    try:
        renderer = get_agent_renderer(selected_page)
        renderer()
    except ValueError as e:
        st.error(f"Navigation error: {e}")
    except Exception as e:
        logger.exception("Unhandled error rendering page '%s': %s", selected_page, e)
        st.error(f"An unexpected error occurred:\n\n{e}")


if __name__ == "__main__":
    main()

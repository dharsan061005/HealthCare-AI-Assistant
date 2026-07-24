"""
Healthcare AI Assistant — Main Streamlit Application
Entry point: streamlit run app.py

Authentication is enforced before any dashboard content is shown.
All existing features (agents, tools, settings) are unchanged.
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
from agents.router import (
    NAV_ITEMS, DEFAULT_PAGE, get_agent_renderer,
    PATIENT_SERVICES, AI_HEALTH_TOOLS, SETTINGS_PAGES,
)
from database.database import init_db
from authentication.auth_db import init_auth_tables
from authentication import session as auth_session
from utils.i18n import LANGUAGES, t
from components.theme_switcher import render_theme_switcher

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


# ─── Helpers ─────────────────────────────────────────────────────────────────

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
            init_auth_tables()          # create users / otp_tokens tables
            from database.family_db import init_family_db
            init_family_db()            # create family.db tables
            st.session_state.db_initialized = True
        except Exception as e:
            st.error(f"**Database Error:** {e}")
            logger.critical("Database init failed: %s", e)
            st.session_state.db_initialized = False


# ─── Auth gate ────────────────────────────────────────────────────────────────

def _render_auth_page() -> None:
    """Render login / register / forgot-password based on session state."""
    page = auth_session.get_auth_page()
    if page == "register":
        from authentication.register import render
        render()
    elif page == "forgot":
        from authentication.forgot_password import render
        render()
    else:
        from authentication.login import render
        render()


# ─── Sidebar user profile card ────────────────────────────────────────────────

def _render_user_profile_sidebar() -> None:
    """Render the user profile card at the top of the sidebar."""
    user     = auth_session.get_current_user()
    initials = auth_session.get_avatar_initials()
    name     = auth_session.get_display_name()
    is_guest = auth_session.is_guest()

    if is_guest:
        st.sidebar.markdown(
            """
            <div class="guest-banner">
              👤 Guest Mode &nbsp;·&nbsp; Limited Access
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        email_display = (user or {}).get("email", "")
        role_label    = "Patient"

        st.sidebar.markdown(
            f"""
            <div class="user-profile-card">
              <div class="user-avatar">{initials}</div>
              <div class="user-display-name">{(user or {}).get('full_name', name)}</div>
              <div class="user-role-badge">
                <span class="user-role-pill">{role_label}</span>
                <span class="user-online-dot"></span>
                <span style="font-size:0.68rem;color:#10B981;font-weight:600;">Online</span>
              </div>
              <div class="user-email-text">{email_display}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.sidebar.divider()

    # Logout button
    st.sidebar.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.sidebar.button("🚪 Logout", key="sidebar_logout", use_container_width=True):
        auth_session.logout()
    st.sidebar.markdown("</div>", unsafe_allow_html=True)

    st.sidebar.divider()


# ─── Main sidebar ─────────────────────────────────────────────────────────────

def _render_sidebar() -> str:
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = DEFAULT_PAGE
    if "ui_language" not in st.session_state:
        st.session_state.ui_language = "English"

    lang = st.session_state.ui_language

    st.sidebar.title(t("app_title", lang))
    st.sidebar.caption(t("app_caption", lang))
    st.sidebar.divider()

    # ── User profile card ─────────────────────────────────────────────────
    _render_user_profile_sidebar()

    # ── Language selector ─────────────────────────────────────────────────
    st.sidebar.markdown(f"**{t('language_selector', lang)}**")
    chosen_lang = st.sidebar.selectbox(
        label="language",
        options=LANGUAGES,
        index=LANGUAGES.index(st.session_state.ui_language),
        key="lang_select",
        label_visibility="collapsed",
    )
    if chosen_lang != st.session_state.ui_language:
        st.session_state.ui_language = chosen_lang
        st.rerun()
    lang = st.session_state.ui_language

    st.sidebar.divider()

    # ── Grouped navigation ────────────────────────────────────────────────
    if st.session_state.selected_page not in NAV_ITEMS:
        st.session_state.selected_page = DEFAULT_PAGE

    # ── 👨‍⚕️ Patient Services ──────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.1em;color:#6B7280;padding:0.2rem 0.75rem 0.1rem;">
        {t("sidebar_patient_services", lang)}
    </div>""", unsafe_allow_html=True)

    ps_selected = st.sidebar.radio(
        label="patient_services",
        options=PATIENT_SERVICES,
        index=PATIENT_SERVICES.index(st.session_state.selected_page)
               if st.session_state.selected_page in PATIENT_SERVICES else 0,
        key="nav_patient",
        label_visibility="collapsed",
        format_func=lambda x: t(x, lang),
    )

    # ✨ NEW badge under Caregiver Management
    st.sidebar.markdown(
        f"""<div style="margin-top:-0.5rem;margin-bottom:0.3rem;padding-left:0.9rem;">
            <span style="font-size:0.62rem;background:#10B981;color:#fff;font-weight:700;
                         border-radius:99px;padding:1px 7px;letter-spacing:0.05em;
                         text-transform:uppercase;">{t("new_badge", lang)}</span>
        </div>""",
        unsafe_allow_html=True,
    )

    st.sidebar.divider()

    # ── 🤖 AI Health Tools ────────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.1em;color:#6B7280;padding:0.2rem 0.75rem 0.1rem;">
        {t("sidebar_ai_tools", lang)}
    </div>""", unsafe_allow_html=True)

    ai_selected = st.sidebar.radio(
        label="ai_health_tools",
        options=AI_HEALTH_TOOLS,
        index=AI_HEALTH_TOOLS.index(st.session_state.selected_page)
               if st.session_state.selected_page in AI_HEALTH_TOOLS else 0,
        key="nav_ai_tools",
        label_visibility="collapsed",
        format_func=lambda x: t(x, lang),
    )

    st.sidebar.divider()

    # ── ⚙️ Settings ───────────────────────────────────────────────────────
    st.sidebar.markdown(f"""
    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.1em;color:#6B7280;padding:0.2rem 0.75rem 0.1rem;">
        {t("sidebar_settings", lang)}
    </div>""", unsafe_allow_html=True)

    settings_selected = st.sidebar.radio(
        label="settings",
        options=SETTINGS_PAGES,
        index=SETTINGS_PAGES.index(st.session_state.selected_page)
               if st.session_state.selected_page in SETTINGS_PAGES else 0,
        key="nav_settings",
        label_visibility="collapsed",
        format_func=lambda x: t(x, lang),
    )

    # ── Determine which group was actually clicked ────────────────────────
    prev = st.session_state.selected_page

    # Initialize last values if not present
    if "last_nav_patient" not in st.session_state:
        st.session_state.last_nav_patient = ps_selected
    if "last_nav_ai_tools" not in st.session_state:
        st.session_state.last_nav_ai_tools = ai_selected
    if "last_nav_settings" not in st.session_state:
        st.session_state.last_nav_settings = settings_selected

    selected = prev

    # If any specific radio widget changed compared to its last known value, update the page
    if ps_selected != st.session_state.last_nav_patient:
        selected = ps_selected
    elif ai_selected != st.session_state.last_nav_ai_tools:
        selected = ai_selected
    elif settings_selected != st.session_state.last_nav_settings:
        selected = settings_selected

    st.session_state.selected_page = selected

    # Sync last values
    st.session_state.last_nav_patient = ps_selected
    st.session_state.last_nav_ai_tools = ai_selected
    st.session_state.last_nav_settings = settings_selected

    # ── System Status ─────────────────────────────────────────────────────
    st.sidebar.divider()
    st.sidebar.markdown(f"**{t('system_status', lang)}**")
    api_ok = bool(config.GROQ_API_KEY)
    db_ok  = st.session_state.get("db_initialized", False)
    st.sidebar.markdown(
        f"{'🟢' if api_ok else '🔴'} {t('groq_active' if api_ok else 'groq_inactive', lang)}"
    )
    st.sidebar.markdown(
        f"{'🟢' if db_ok else '🔴'} {t('db_connected' if db_ok else 'db_error', lang)}"
    )
    if db_ok:
        try:
            from database.database import count_caregivers
            cg_count = count_caregivers(active_only=True)
            st.sidebar.markdown(t("caregivers_active", lang).replace("{n}", str(cg_count)))
        except Exception:
            pass

    st.sidebar.divider()
    st.sidebar.caption(t("ai_disclaimer", lang))

    return selected


# ─── Main entry point ─────────────────────────────────────────────────────────

def main() -> None:
    _load_css()
    _ensure_db_initialized()

    # ── Auth gate: show login/register/forgot if not authenticated ────────
    if not auth_session.is_logged_in():
        _render_auth_page()
        return  # stop here — do NOT render the dashboard

    # ── Authenticated: render full dashboard ──────────────────────────────
    selected_page = _render_sidebar()

    # ── Render theme switcher (floating widget) ───────────────────────────
    render_theme_switcher()

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

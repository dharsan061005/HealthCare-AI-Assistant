"""
Settings Agent — app preferences, SMTP config guidance, language info.
"""
import logging

import streamlit as st

import config
from utils.i18n import LANGUAGES, get_lang, t

logger = logging.getLogger(__name__)


def render() -> None:
    lang = get_lang(st.session_state)

    st.markdown(f"""
    <div class="page-header">
        <div style="display:flex;align-items:center;gap:1rem;">
            <span style="font-size:2.2rem;">⚙️</span>
            <div>
                <h1 style="margin:0;">{t("settings_title", lang)}</h1>
                <p style="margin:0;">{t("settings_subtitle", lang)}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["🌐 Language", "🔑 API & Email", "ℹ️ About"])

    # ── Language tab ──────────────────────────────────────────────────────────
    with tabs[0]:
        st.markdown("#### 🌐 Interface Language")
        st.markdown(
            "Choose your preferred language. All UI labels, buttons, and messages "
            "will switch immediately. Text you type in any field is always accepted "
            "in any script regardless of this setting."
        )
        current = st.session_state.get("ui_language", "English")
        chosen = st.selectbox(
            "Select Language",
            options=LANGUAGES,
            index=LANGUAGES.index(current),
            key="settings_lang_select",
        )
        if st.button("💾 Apply Language", type="primary"):
            st.session_state.ui_language = chosen
            st.success(f"Language set to **{chosen}**. Refreshing…")
            st.rerun()

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("**Supported Languages:**")
        cols = st.columns(4)
        for i, lng in enumerate(LANGUAGES):
            cols[i % 4].markdown(
                f"<div style='background:#F0F9FF;border:1px solid #BAE6FD;border-radius:8px;"
                f"padding:0.5rem 0.75rem;font-size:0.85rem;margin-bottom:0.5rem;"
                f"text-align:center;'>{lng}</div>",
                unsafe_allow_html=True,
            )

    # ── API & Email tab ───────────────────────────────────────────────────────
    with tabs[1]:
        st.markdown("#### 🔑 System Configuration")

        api_ok = bool(config.GROQ_API_KEY)
        st.markdown(f"""
        <div style="background:{'#F0FDF4' if api_ok else '#FEF2F2'};
                    border:1px solid {'#BBF7D0' if api_ok else '#FECACA'};
                    border-radius:10px;padding:1rem 1.25rem;margin-bottom:1rem;">
            <div style="font-weight:700;color:{'#15803D' if api_ok else '#991B1B'};">
                {'✅' if api_ok else '❌'} Groq API Key — {'Configured' if api_ok else 'Not Set'}
            </div>
            {'<div style="font-size:0.83rem;color:#475569;margin-top:0.4rem;">Key: ' + config.GROQ_API_KEY[:12] + '…</div>' if api_ok else '<div style="font-size:0.83rem;color:#475569;margin-top:0.4rem;">Add GROQ_API_KEY to your .env file. Get a key at console.groq.com/keys</div>'}
        </div>
        """, unsafe_allow_html=True)

        import os
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_pw   = os.getenv("SMTP_PASSWORD", "")
        placeholders = {"your@gmail.com", "your-app-password", ""}
        email_ok = smtp_user not in placeholders and smtp_pw not in placeholders
        st.markdown(f"""
        <div style="background:{'#F0FDF4' if email_ok else '#FFF7ED'};
                    border:1px solid {'#BBF7D0' if email_ok else '#FED7AA'};
                    border-radius:10px;padding:1rem 1.25rem;margin-bottom:1rem;">
            <div style="font-weight:700;color:{'#15803D' if email_ok else '#92400E'};">
                {'✅' if email_ok else '⚠️'} Email (SMTP) — {'Configured' if email_ok else 'Using Simulation Mode'}
            </div>
            <div style="font-size:0.83rem;color:#475569;margin-top:0.4rem;">
                {'Sender: ' + smtp_user if email_ok else 'To send real emails, set SMTP_USER and SMTP_PASSWORD (Gmail App Password) in your .env file.'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("📋 How to configure Gmail App Password"):
            st.markdown("""
            1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
            2. Select **Mail** and your device
            3. Copy the 16-character app password
            4. Add to your `.env` file:
            ```
            SMTP_HOST=smtp.gmail.com
            SMTP_PORT=587
            SMTP_USER=your@gmail.com
            SMTP_PASSWORD=your-16-char-app-password
            ```
            5. Restart the app with `start.bat`
            """)

    # ── About tab ─────────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#EFF6FF,#DBEAFE);border:1px solid #BFDBFE;
                    border-radius:16px;padding:2rem;text-align:center;margin-bottom:1.5rem;">
            <div style="font-size:3rem;margin-bottom:0.5rem;">🏥</div>
            <div style="font-size:1.4rem;font-weight:800;color:#1E40AF;">Healthcare AI Assistant</div>
            <div style="font-size:0.9rem;color:#3B82F6;margin-top:0.25rem;">
                v{config.APP_VERSION} — AI-powered healthcare companion
            </div>
        </div>
        """, unsafe_allow_html=True)

        features = [
            ("🏥", "Hospital Information",    "Browse departments, doctors, and facilities"),
            ("📅", "Appointment Scheduling",  "Book, view, cancel, and reschedule visits"),
            ("🩺", "Symptom Checker",         "AI-powered symptom analysis"),
            ("📄", "Report Summarizer",       "Upload medical PDFs for AI summaries"),
            ("💊", "Prescription Reminders",  "Medicine schedule with caregiver alerts"),
            ("👨‍👩‍👧", "Caregiver Management",  "Patient companion notifications"),
            ("🏥", "AI Health Assistant",     "Conversational general health guidance"),
            ("💊", "Medicine Information",    "AI-powered drug lookup"),
            ("📖", "Medical Dictionary",      "Plain-language medical term definitions"),
            ("🚑", "Emergency Help",          "Emergency numbers and first-aid guides"),
        ]
        cols = st.columns(2)
        for i, (icon, title, desc) in enumerate(features):
            with cols[i % 2]:
                st.markdown(f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;
                            padding:0.85rem 1rem;margin-bottom:0.6rem;display:flex;gap:0.75rem;">
                    <span style="font-size:1.3rem;">{icon}</span>
                    <div>
                        <div style="font-weight:700;font-size:0.88rem;color:#0F172A;">{title}</div>
                        <div style="font-size:0.8rem;color:#64748B;">{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center;margin-top:1.5rem;font-size:0.8rem;color:#94A3B8;">
            Built with Streamlit · Groq LLM · SQLite · Python
        </div>
        """, unsafe_allow_html=True)

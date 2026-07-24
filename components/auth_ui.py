"""
Shared Auth UI helpers — Healthcare AI Assistant v2.0
Premium dark glassmorphism card for login / register / forgot-password.
"""

import streamlit as st

AUTH_CSS = """
<style>
/* ── Hide sidebar on auth pages ─────────────────────────── */
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* ── Full-page dark background ──────────────────────────── */
[data-testid="stAppViewContainer"] {
  background: radial-gradient(ellipse at 20% 30%, rgba(59,130,246,0.12) 0%, transparent 50%),
              radial-gradient(ellipse at 80% 70%, rgba(59,130,246,0.08) 0%, transparent 50%),
              linear-gradient(160deg, #050913 0%, #0A0F1E 50%, #070C18 100%) !important;
  min-height: 100vh;
}

[data-testid="stAppViewContainer"] > .main {
  background: transparent !important;
}

/* ── Strip white boxes ───────────────────────────────────── */
[data-testid="stForm"],
[data-testid="stVerticalBlockBorderWrapper"],
section[data-testid="stForm"] {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.main .block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* ── Global text — light on dark ────────────────────────── */
[data-testid="stAppViewContainer"] .main p,
[data-testid="stAppViewContainer"] .main span,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span {
  color: #CBD5E1 !important;
  font-weight: 500 !important;
}

[data-testid="stAppViewContainer"] .main h1,
[data-testid="stAppViewContainer"] .main h2,
[data-testid="stAppViewContainer"] .main h3 {
  color: #FFFFFF !important;
  font-weight: 800 !important;
}

/* ── Widget labels ───────────────────────────────────────── */
.stTextInput label, .stTextInput label p,
.stNumberInput label, .stNumberInput label p,
.stSelectbox label, .stSelectbox label p,
.stCheckbox label, .stCheckbox label p,
.stCheckbox span,
div[data-baseweb="form-control"] label,
div[data-baseweb="form-control"] label p {
  color: #CBD5E1 !important;
  font-weight: 600 !important;
}

[data-testid="column"] p,
[data-testid="column"] span,
[data-testid="column"] label { color: #CBD5E1 !important; font-weight: 600 !important; }

/* ── Layout ──────────────────────────────────────────────── */
.auth-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem 1rem;
}

/* ── Glassmorphism card ──────────────────────────────────── */
.auth-card {
  background: rgba(15, 23, 42, 0.85) !important;
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 24px;
  padding: 2.5rem 2.5rem 2rem;
  width: 100%;
  max-width: 460px;
  box-shadow: 0 30px 80px rgba(0,0,0,0.7),
              0 0 0 1px rgba(59,130,246,0.1) inset,
              0 0 60px rgba(59,130,246,0.05);
  position: relative;
  overflow: hidden;
  animation: cardSlideIn 0.45s cubic-bezier(0.34,1.56,0.64,1) both;
}

.auth-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(59,130,246,0.6), transparent);
}

@keyframes cardSlideIn {
  from { opacity: 0; transform: translateY(32px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* ── Logo ────────────────────────────────────────────────── */
.auth-logo {
  width: 70px; height: 70px;
  background: linear-gradient(135deg, #3B82F6, #2563EB);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.9rem;
  margin: 0 auto 1.2rem;
  box-shadow: 0 8px 28px rgba(59,130,246,0.5);
  animation: logoPulse 2.5s ease-in-out infinite;
}

@keyframes logoPulse {
  0%, 100% { box-shadow: 0 8px 28px rgba(59,130,246,0.5); }
  50%      { box-shadow: 0 8px 40px rgba(59,130,246,0.8); }
}

/* ── Title ───────────────────────────────────────────────── */
.auth-title {
  text-align: center;
  font-size: 1.5rem !important;
  font-weight: 800 !important;
  color: #FFFFFF !important;
  margin: 0 0 0.15rem !important;
  letter-spacing: -0.02em;
}

.auth-subtitle {
  text-align: center;
  font-size: 0.86rem !important;
  font-weight: 500 !important;
  color: #64748B !important;
  margin: 0 0 1.75rem !important;
}

/* ── Field labels ────────────────────────────────────────── */
.field-label, p.field-label {
  font-size: 0.7rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.1em !important;
  text-transform: uppercase !important;
  color: #94A3B8 !important;
  -webkit-text-fill-color: #94A3B8 !important;
  margin: 0 0 0.2rem !important;
  padding: 0 !important;
}

/* ── Input fields ────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
  background: rgba(30,41,59,0.9) !important;
  border: 1.5px solid rgba(255,255,255,0.08) !important;
  color: #F8FAFC !important;
  -webkit-text-fill-color: #F8FAFC !important;
  font-weight: 500 !important;
  font-size: 0.93rem !important;
  border-radius: 12px !important;
  caret-color: #3B82F6 !important;
}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
  border-color: #3B82F6 !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.25) !important;
  background: rgba(30,41,59,1) !important;
  outline: none !important;
}

.stTextInput > div > div > input::placeholder,
.stNumberInput > div > div > input::placeholder {
  color: #475569 !important;
  -webkit-text-fill-color: #475569 !important;
  font-weight: 400 !important;
}

/* ── Selectbox ───────────────────────────────────────────── */
.stSelectbox > div > div {
  background: rgba(30,41,59,0.9) !important;
  border: 1.5px solid rgba(255,255,255,0.08) !important;
  border-radius: 12px !important;
  color: #F8FAFC !important;
  font-weight: 500 !important;
}

.stSelectbox > div > div > div,
.stSelectbox > div > div span {
  color: #F8FAFC !important;
  font-weight: 500 !important;
  -webkit-text-fill-color: #F8FAFC !important;
}

/* ── Buttons ─────────────────────────────────────────────── */

/* Primary button */
.stButton > button[kind="primary"] {
  width: 100%;
  padding: 0.72rem 1rem !important;
  font-size: 0.95rem !important;
  font-weight: 700 !important;
  border-radius: 12px !important;
  background: linear-gradient(135deg, #3B82F6, #2563EB) !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  border: none !important;
  box-shadow: 0 4px 20px rgba(59,130,246,0.45) !important;
  transition: all 0.2s !important;
}

.stButton > button[kind="primary"]:hover {
  background: linear-gradient(135deg, #60A5FA, #3B82F6) !important;
  box-shadow: 0 6px 28px rgba(59,130,246,0.65) !important;
  transform: translateY(-2px) scale(1.01) !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
}

/* Secondary button */
.stButton > button:not([kind="primary"]) {
  padding: 0.58rem 1rem !important;
  font-size: 0.87rem !important;
  font-weight: 600 !important;
  border-radius: 12px !important;
  background: rgba(255,255,255,0.07) !important;
  color: #E2E8F0 !important;
  -webkit-text-fill-color: #E2E8F0 !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
  transition: all 0.2s !important;
  box-shadow: none !important;
}

.stButton > button:not([kind="primary"]):hover {
  background: rgba(255,255,255,0.12) !important;
  color: #FFFFFF !important;
  -webkit-text-fill-color: #FFFFFF !important;
  border-color: rgba(255,255,255,0.25) !important;
}

/* Link / anchor buttons */
.auth-link-btn .stButton > button {
  background: none !important;
  border: none !important;
  color: #60A5FA !important;
  -webkit-text-fill-color: #60A5FA !important;
  font-size: 0.84rem !important;
  font-weight: 600 !important;
  padding: 0 !important;
  box-shadow: none !important;
  text-decoration: underline !important;
  width: auto !important;
}

.auth-link-btn .stButton > button:hover {
  color: #93C5FD !important;
  -webkit-text-fill-color: #93C5FD !important;
  background: none !important;
  transform: none !important;
}

/* ── Checkbox ─────────────────────────────────────────────── */
.stCheckbox > label,
.stCheckbox > label > div,
.stCheckbox > label span,
.stCheckbox > label p {
  color: #CBD5E1 !important;
  -webkit-text-fill-color: #CBD5E1 !important;
  font-size: 0.84rem !important;
  font-weight: 500 !important;
}

/* ── Feedback pills ──────────────────────────────────────── */
.auth-error {
  background: rgba(239,68,68,0.15);
  border: 1px solid rgba(239,68,68,0.35);
  border-radius: 10px;
  padding: 0.65rem 0.9rem;
  color: #FCA5A5 !important;
  font-weight: 600 !important;
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
  animation: fadeIn 0.3s ease;
}

.auth-success {
  background: rgba(34,197,94,0.12);
  border: 1px solid rgba(34,197,94,0.3);
  border-radius: 10px;
  padding: 0.65rem 0.9rem;
  color: #86EFAC !important;
  font-weight: 600 !important;
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
  animation: fadeIn 0.3s ease;
}

.auth-info {
  background: rgba(59,130,246,0.12);
  border: 1px solid rgba(59,130,246,0.25);
  border-radius: 10px;
  padding: 0.65rem 0.9rem;
  color: #93C5FD !important;
  font-weight: 600 !important;
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-5px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── OR divider ──────────────────────────────────────────── */
.auth-divider {
  display: flex; align-items: center; gap: 0.75rem; margin: 1.2rem 0;
}

.auth-divider-line {
  flex: 1; height: 1px;
  background: rgba(255,255,255,0.1);
}

.auth-divider-text {
  font-size: 0.78rem;
  font-weight: 700 !important;
  color: #475569 !important;
  -webkit-text-fill-color: #475569 !important;
  white-space: nowrap;
}

/* ── Bottom nav text ─────────────────────────────────────── */
.auth-bottom-text, p.auth-bottom-text {
  text-align: center;
  color: #64748B !important;
  -webkit-text-fill-color: #64748B !important;
  font-weight: 500 !important;
  font-size: 0.84rem;
  margin-top: 1.2rem;
}

/* ── Password strength bar ───────────────────────────────── */
.strength-bar-wrap  { margin-top: -0.3rem; margin-bottom: 0.5rem; }
.strength-bar-track { height: 4px; background: rgba(255,255,255,0.08); border-radius: 99px; overflow: hidden; }
.strength-bar-fill  { height: 100%; border-radius: 99px; transition: width 0.3s ease; }
.strength-label     { font-size: 0.7rem; font-weight: 700; margin-top: 2px; text-align: right; }

/* ── Step indicator ──────────────────────────────────────── */
.auth-steps { display: flex; justify-content: center; gap: 0.5rem; margin-bottom: 1.5rem; }
.auth-step {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 800;
}
.auth-step.active  { background: #3B82F6; color: #FFF !important; -webkit-text-fill-color: #FFF !important; box-shadow: 0 4px 12px rgba(59,130,246,0.5); }
.auth-step.done    { background: #22C55E; color: #FFF !important; -webkit-text-fill-color: #FFF !important; }
.auth-step.pending { background: rgba(255,255,255,0.08); color: #64748B !important; -webkit-text-fill-color: #64748B !important; border: 1px solid rgba(255,255,255,0.12); }
.auth-step-line    { width: 32px; height: 2px; background: rgba(255,255,255,0.1); align-self: center; }

/* ── Misc ─────────────────────────────────────────────────── */
.otp-hint {
  text-align: center;
  color: #94A3B8 !important;
  -webkit-text-fill-color: #94A3B8 !important;
  font-weight: 600 !important;
  font-size: 0.82rem;
  margin-bottom: 0.75rem;
}
[data-testid="stSpinner"] > div { border-top-color: #3B82F6 !important; }
.stCaption, [data-testid="stCaptionContainer"] { color: #64748B !important; -webkit-text-fill-color: #64748B !important; }
</style>
"""


def inject_auth_css() -> None:
    st.markdown(AUTH_CSS, unsafe_allow_html=True)


def auth_card_open() -> None:
    st.markdown(
        """
        <div class="auth-wrapper">
          <div class="auth-card">
            <div class="auth-logo">🏥</div>
            <h1 class="auth-title">Healthcare AI Assistant</h1>
            <p class="auth-subtitle">Your Smart Healthcare Companion</p>
        """,
        unsafe_allow_html=True,
    )


def auth_card_close() -> None:
    st.markdown("</div></div>", unsafe_allow_html=True)


def auth_error(message: str) -> None:
    st.markdown(f'<div class="auth-error">⚠️ {message}</div>', unsafe_allow_html=True)


def auth_success(message: str) -> None:
    st.markdown(f'<div class="auth-success">✅ {message}</div>', unsafe_allow_html=True)


def auth_info(message: str) -> None:
    st.markdown(f'<div class="auth-info">ℹ️ {message}</div>', unsafe_allow_html=True)


def divider_or() -> None:
    st.markdown(
        """
        <div class="auth-divider">
          <div class="auth-divider-line"></div>
          <span class="auth-divider-text">OR</span>
          <div class="auth-divider-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_strength_bar(password: str) -> None:
    if not password:
        return
    from authentication.auth import password_strength_label
    label, colour = password_strength_label(password)
    pct = {"Weak": 25, "Fair": 50, "Good": 75, "Strong": 100}.get(label, 0)
    st.markdown(
        f"""
        <div class="strength-bar-wrap">
          <div class="strength-bar-track">
            <div class="strength-bar-fill" style="width:{pct}%;background:{colour};"></div>
          </div>
          <div class="strength-label" style="color:{colour};">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_indicator(current: int, total: int = 3) -> None:
    labels = ["📧", "🔑", "🔒"]
    html = '<div class="auth-steps">'
    for i in range(1, total + 1):
        if i < current:
            cls, lbl = "done",    "✓"
        elif i == current:
            cls, lbl = "active",  labels[i - 1]
        else:
            cls, lbl = "pending", str(i)
        html += f'<div class="auth-step {cls}">{lbl}</div>'
        if i < total:
            html += '<div class="auth-step-line"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

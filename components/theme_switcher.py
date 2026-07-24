"""
Theme Switcher Component — Healthcare AI Assistant
Allows user to switch between Blue, Red, and Green accent themes.
"""

import streamlit as st


def render_theme_switcher() -> None:
    """
    Render a floating theme switcher widget.
    User can click to switch between Blue, Red, Green themes.
    """
    # Initialize theme in session state
    if "app_theme" not in st.session_state:
        st.session_state.app_theme = "blue"  # Default

    current_theme = st.session_state.app_theme

    # Theme switcher HTML + JS
    st.markdown(
        f"""
        <div class="theme-switcher" id="themeSwitcher">
            <button class="theme-btn theme-btn-blue {'active' if current_theme == 'blue' else ''}" 
                    onclick="switchTheme('blue')" title="Blue Theme">
                💙
            </button>
            <button class="theme-btn theme-btn-red {'active' if current_theme == 'red' else ''}" 
                    onclick="switchTheme('red')" title="Red Theme">
                ❤️
            </button>
            <button class="theme-btn theme-btn-green {'active' if current_theme == 'green' else ''}" 
                    onclick="switchTheme('green')" title="Green Theme">
                💚
            </button>
        </div>

        <script>
        function switchTheme(theme) {{
            // Apply data-theme attribute to root
            if (theme === 'blue') {{
                document.documentElement.removeAttribute('data-theme');
            }} else {{
                document.documentElement.setAttribute('data-theme', theme);
            }}

            // Update active button
            document.querySelectorAll('.theme-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            document.querySelector('.theme-btn-' + theme).classList.add('active');

            // Store preference
            localStorage.setItem('healthcareAppTheme', theme);

            // Notify Streamlit (optional — we'll sync via session_state separately if needed)
            // For now, theme persists via CSS only
        }}

        // On page load, restore saved theme
        (function() {{
            const saved = localStorage.getItem('healthcareAppTheme') || 'blue';
            switchTheme(saved);
        }})();
        </script>
        """,
        unsafe_allow_html=True,
    )


def get_current_theme() -> str:
    """Return the current theme name (blue, red, or green)."""
    return st.session_state.get("app_theme", "blue")

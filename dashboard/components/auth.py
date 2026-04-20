"""Authentication helpers for role-based access.

Two shared passwords (owner / sales) live in st.secrets["auth"].
Password comparison uses hmac.compare_digest to avoid timing attacks.
Session state keys:
  role       — "owner" | "sales" | absent
  authed_at  — float timestamp from time.time()
"""
import hmac
import time
import streamlit as st


_ROLE_OWNER = "owner"
_ROLE_SALES = "sales"
_VALID_ROLES = (_ROLE_OWNER, _ROLE_SALES)


def _get_secret(key):
    """Return st.secrets['auth'][key] or None if missing. Never raises."""
    try:
        return st.secrets["auth"][key]
    except Exception:
        return None


def _secrets_configured():
    return (
        bool(_get_secret("owner_password"))
        and bool(_get_secret("sales_password"))
        and bool(_get_secret("owner_email"))
        and bool(_get_secret("sales_email"))
    )


def _role_for_email(email):
    """Map an email (case-insensitive, trimmed) to a role, or None."""
    if not email:
        return None
    normalized = email.strip().lower()
    if normalized == (_get_secret("owner_email") or "").strip().lower():
        return _ROLE_OWNER
    if normalized == (_get_secret("sales_email") or "").strip().lower():
        return _ROLE_SALES
    return None


def current_role():
    """Return the active role or None if not logged in."""
    return st.session_state.get("role")


def _check_password(entered, stored):
    if stored is None:
        return False
    return hmac.compare_digest(entered.encode("utf-8"), stored.encode("utf-8"))


def render_login():
    """Render the centered-card login. Must run when role is unset."""
    from dashboard.components.theme import inject_css, current_theme
    import streamlit as st

    st.markdown(inject_css(current_theme()), unsafe_allow_html=True)

    if not _secrets_configured():
        st.error(
            "Authentication is not configured. "
            "Contact the administrator — `st.secrets['auth']` is missing "
            "required email/password entries."
        )
        st.stop()

    # Center the form in a narrow column; brand + subtitle sit above the form card.
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown(
            '<div class="tx-login-title">TEXICON<span class="tx-leaf"></span></div>'
            '<div class="tx-login-sub">Sign in to continue</div>',
            unsafe_allow_html=True,
        )
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@texicon.com",
                                  label_visibility="collapsed")
            password = st.text_input("Password", type="password",
                                     placeholder="Password",
                                     label_visibility="collapsed")
            submitted = st.form_submit_button("Sign in",
                                              use_container_width=True,
                                              type="primary")

    if submitted:
        role_key = _role_for_email(email)
        stored = _get_secret(f"{role_key}_password") if role_key else None
        if role_key and _check_password(password, stored):
            st.session_state["role"] = role_key
            st.session_state["authed_at"] = time.time()
            st.rerun()
        else:
            with mid:
                st.error("Invalid email or password.")

    st.stop()


def require_role(allowed):
    """Guard a page. Call immediately after st.set_page_config + CSS block.

    `allowed` is a list like ["owner"], ["sales"], or ["owner", "sales"].
    - If role unset → show "please log in" and stop.
    - If role not in allowed → show "not authorized" and stop.
    - Otherwise return normally.
    """
    role = current_role()
    if role is None:
        st.markdown("### Please log in")
        st.markdown("Return to the [Executive home](/) to sign in.")
        st.stop()
    if role not in allowed:
        st.markdown("### Not authorized")
        st.markdown(
            f"Your role (`{role}`) does not have access to this page. "
            "Please navigate using the menu."
        )
        st.stop()


def logout_button(key="logout_btn"):
    """Render a Log out button. On click, clear session state and rerun."""
    if st.button("Log out", key=key, use_container_width=False):
        st.session_state.clear()
        st.rerun()


def user_chip():
    """Render a small role chip + logout button on the right side of the page.

    Call once per page, immediately after top_bar(). Uses a 2-column layout
    so the chip floats to the right.
    """
    role = current_role()
    if role is None:
        return
    label = "Owner" if role == _ROLE_OWNER else "Sales"
    c1, c2 = st.columns([6, 1])
    with c1:
        st.markdown(
            f'<div style="font-size:0.78rem;color:var(--text-secondary);'
            f'margin-top:4px;">Logged in as <strong>{label}</strong></div>',
            unsafe_allow_html=True,
        )
    with c2:
        logout_button()

import streamlit as st


def is_authenticated():
    """Check whether the current user is authenticated."""
    return st.session_state.get("authenticated", False)


def get_current_username():
    """Return the username of the logged-in user."""
    return st.session_state.get("username")


def get_current_name():
    """Return the name of the logged-in user."""
    return st.session_state.get("name")


def get_current_role():
    """Return the role of the logged-in user."""
    return st.session_state.get("role")


def require_login():
    """
    Prevent access to a page when the user is not authenticated.
    """

    if not is_authenticated():

        st.error(
            "🔒 Access denied. Please log in to use this page."
        )

        st.stop()


def require_role(allowed_roles):
    """
    Allow access only to users with one of the specified roles.
    """

    require_login()

    current_role = get_current_role()

    if current_role not in allowed_roles:

        st.error(
            "⛔ You do not have permission to access this page."
        )

        st.info(
            f"Your current role is: {current_role}"
        )

        st.stop()


def logout():
    """Log the current user out."""

    for key in [
        "authenticated",
        "username",
        "name",
        "role"
    ]:

        st.session_state.pop(key, None)

import streamlit as st

from utils.security import verify_password
from utils.users import USERS


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Login | Family Planning Management System",
    page_icon="🏥",
    layout="centered",
)


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title(
    "🏥 Family Planning Management System"
)

st.subheader(
    "Njoro Sub-County Hospital"
)

st.write(
    "Secure access to the Family Planning Management System."
)

st.divider()


# --------------------------------------------------
# Login section
# --------------------------------------------------

st.markdown("### 🔐 User Login")

st.caption(
    "Enter your authorized credentials to continue."
)


with st.form("login_form"):

    username = st.text_input(
        "Username",
        placeholder="Enter your username",
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
    )

    login_button = st.form_submit_button(
        "🔐 Login",
        type="primary",
        use_container_width=True,
    )


# --------------------------------------------------
# Authentication
# --------------------------------------------------

if login_button:

    username = username.strip().lower()

    if not username or not password:

        st.warning(
            "Please enter both your username and password."
        )

    elif username in USERS:

        user = USERS[username]

        if verify_password(
            password,
            user["password_hash"],
        ):

            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["name"] = user["name"]
            st.session_state["role"] = user["role"]

            st.success(
                f"Login successful. Welcome, {user['name']}."
            )

            st.info(
                f"Role: {user['role']}"
            )

            st.caption(
                "You may now use the modules available "
                "to your assigned role."
            )

        else:

            st.error(
                "Invalid username or password."
            )

    else:

        st.error(
            "Invalid username or password."
        )


# --------------------------------------------------
# Security notice
# --------------------------------------------------

st.divider()

st.markdown("### 🔒 Security Notice")

st.caption(
    "This system is restricted to authorized users. "
    "Access to system modules is controlled according "
    "to the user's assigned role."
)


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption(
    "Family Planning Management System | "
    "Njoro Sub-County Hospital"
)

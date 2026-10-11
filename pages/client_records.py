import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import date


from utils.auth import (
    require_login,
    get_current_name,
    get_current_role
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Client Records | Family Planning Management System",
    page_icon="👩‍⚕️",
    layout="wide"
)

require_login()


# =========================================================
# ROLE INFORMATION
# =========================================================

current_role = get_current_role()
current_name = get_current_name()

CLIENT_VIEW_ROLES = [
    "FP Service Provider",
    "Supervisor",
    "Administrator",
    "Pharmacy/Commodity Officer"
]

CLIENT_EDIT_ROLES = [
    "FP Service Provider",
    "Supervisor",
    "Administrator"
]

if current_role not in CLIENT_VIEW_ROLES:
    st.error(
        "⛔ You do not have permission to access Client Records."
    )
    st.stop()

can_edit_clients = current_role in CLIENT_EDIT_ROLES


# =========================================================
# FILE CONFIGURATION
# =========================================================

DATA_PATH = Path("data/service_records.csv")

EXPECTED_COLUMNS = [
    "client_id",
    "encounter_id",
    "date",
    "month",
    "sex",
    "age",
    "client_type",
    "first_ever_user",
    "method",
    "visit_type_for_method",
    "quantity_dispensed",
    "client_count",
    "counselled_for_fp",
    "counselled_for_hiv",
    "hiv_tested",
    "hiv_status",
    "ppfp_timing",
    "tb_screening",
    "cervical_cancer_screening",
    "referral"
]


# =========================================================
# CUSTOM STYLING
# =========================================================

st.markdown(
    """
    <style>

    .section-card {
        padding: 1rem 1.2rem;
        border: 1px solid #d9d9d9;
        border-radius: 10px;
        margin-bottom: 1rem;
        background-color: #ffffff;
    }

    .id-card {
        padding: 1rem 1.2rem;
        border-radius: 10px;
        border: 1px solid #d9d9d9;
        background-color: #f7f7f7;
        margin-bottom: 1rem;
    }

    .client-id {
        font-size: 24px;
        font-weight: 700;
    }

    .encounter-id {
        font-size: 18px;
        font-weight: 600;
    }

    .small-note {
        color: #666666;
        font-size: 14px;
    }

    .fp-table-wrapper {
        width: 100%;
        overflow-x: auto;
        margin: 0.5rem 0 1.2rem 0;
        border: 1px solid #d9d9d9;
        border-radius: 8px;
        background: #ffffff;
    }

    .fp-record-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }

    .fp-record-table th {
        text-align: left;
        padding: 10px 12px;
        border-bottom: 2px solid #d9d9d9;
        background: #f5f7f9;
        font-weight: 700;
        white-space: nowrap;
    }

    .fp-record-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #e5e5e5;
        white-space: nowrap;
    }

    .fp-record-table tbody tr:last-child td {
        border-bottom: none;
    }

    .fp-record-table tbody tr:hover {
        background: #f8f9fa;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# STYLED TABLE DISPLAY
# =========================================================

def display_styled_table(dataframe):
    """
    Display a clean, professional HTML table for
    client and encounter records.
    """

    if dataframe.empty:
        st.info("No records to display.")
        return

    html_table = dataframe.to_html(
        index=False,
        escape=True,
        classes="fp-record-table",
        border=0
    )

    st.markdown(
        f"""
        <div class="fp-table-wrapper">
            {html_table}
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# DATA FUNCTIONS
# =========================================================

def load_data():

    if not DATA_PATH.exists():

        return pd.DataFrame(
            columns=EXPECTED_COLUMNS
        )

    df = pd.read_csv(DATA_PATH)

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    df = df[EXPECTED_COLUMNS].copy()

    return df


def save_data(df):

    df.to_csv(
        DATA_PATH,
        index=False
    )


df = load_data()


# =========================================================
# ID GENERATION
# =========================================================

def generate_next_client_id(dataframe):

    if dataframe.empty:
        return "FP-NJR-000001"

    numbers = []

    for value in dataframe["client_id"].dropna():

        value = str(value)

        if value.startswith("FP-NJR-"):

            try:

                number = int(
                    value.replace(
                        "FP-NJR-",
                        ""
                    )
                )

                numbers.append(number)

            except ValueError:
                pass

    next_number = max(
        numbers,
        default=0
    ) + 1

    return f"FP-NJR-{next_number:06d}"


def generate_next_encounter_id(dataframe):

    if dataframe.empty:
        return "ENC-FP-NJR-000001"

    numbers = []

    for value in dataframe["encounter_id"].dropna():

        value = str(value)

        if value.startswith("ENC-FP-NJR-"):

            try:

                number = int(
                    value.replace(
                        "ENC-FP-NJR-",
                        ""
                    )
                )

                numbers.append(number)

            except ValueError:
                pass

    next_number = max(
        numbers,
        default=0
    ) + 1

    return f"ENC-FP-NJR-{next_number:06d}"


# =========================================================
# SESSION STATE
# =========================================================

if "selected_client_id" not in st.session_state:

    st.session_state.selected_client_id = ""


if "client_search_message" not in st.session_state:

    st.session_state.client_search_message = ""


if "save_success_message" not in st.session_state:

    st.session_state.save_success_message = ""


# =========================================================
# PAGE HEADER
# =========================================================

st.title(
    "👩‍⚕️ FP Client & Service Records"
)

st.write(
    "Manage family planning clients and record "
    "individual service encounters."
)

st.caption(
    f"Logged in as: {current_name} | "
    f"Role: {current_role}"
)


# =========================================================
# SUMMARY METRICS
# =========================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Recorded Encounters",
        len(df)
    )

with col2:

    st.metric(
        "Registered Client IDs",
        df["client_id"].nunique()
        if not df.empty
        else 0
    )

with col3:

    st.metric(
        "Latest Encounter",
        df["encounter_id"].iloc[-1]
        if not df.empty
        else "None"
    )


st.divider()


# =========================================================
# DISPLAY SAVE MESSAGE
# =========================================================

if st.session_state.save_success_message:

    st.success(
        st.session_state.save_success_message
    )

    st.session_state.save_success_message = ""


# =========================================================
# WORKFLOW SELECTION
# =========================================================

if can_edit_clients:

    st.subheader(
        "Choose Client Workflow"
    )

    workflow = st.radio(
        "Select an action",
        [
            "🔎 Find Existing Client",
            "➕ Register New Client"
        ],
        horizontal=True
    )

else:

    workflow = "🔎 Find Existing Client"

    st.info(
        "You have read-only access to Client Records."
    )


# =========================================================
# FIND EXISTING CLIENT
# =========================================================

if workflow == "🔎 Find Existing Client":

    st.subheader(
        "🔎 Find Existing Client"
    )

    st.write(
        "Search using the client's unique Client ID."
    )

    search_col1, search_col2 = st.columns(
        [3, 1]
    )

    with search_col1:

        search_client_id = st.text_input(
            "Client ID",
            value=st.session_state.selected_client_id,
            placeholder="Example: FP-NJR-000127",
            help="Enter the client's unique Client ID."
        ).strip().upper()

    with search_col2:

        st.write("")

        search_button = st.button(
            "🔎 Search Client",
            use_container_width=True
        )

    if search_button:

        if not search_client_id:

            st.warning(
                "Please enter a Client ID."
            )

            st.session_state.selected_client_id = ""

        else:

            matches = df[
                df["client_id"].astype(str).str.upper()
                == search_client_id
            ]

            if matches.empty:

                st.error(
                    f"No client found with ID: "
                    f"{search_client_id}"
                )

                st.session_state.selected_client_id = ""

            else:

                st.session_state.selected_client_id = (
                    search_client_id
                )

                st.session_state.client_search_message = (
                    "Client found."
                )

                st.rerun()


    # -----------------------------------------------------
    # LOAD SELECTED CLIENT
    # -----------------------------------------------------

    selected_client_id = (
        st.session_state.selected_client_id
    )

    if selected_client_id:

        matches = df[
            df["client_id"].astype(str).str.upper()
            == selected_client_id
        ]

        if not matches.empty:

            client = matches.iloc[0]

            st.success(
                f"Client found: {selected_client_id}"
            )

            st.markdown(
                f"""
                <div class="id-card">

                <div class="small-note">
                Client ID
                </div>

                <div class="client-id">
                {client["client_id"]}
                </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            info1, info2, info3 = st.columns(3)

            with info1:

                st.metric(
                    "Sex",
                    client["sex"]
                )

            with info2:

                st.metric(
                    "Age",
                    int(client["age"])
                )

            with info3:

                st.metric(
                    "Recorded Encounters",
                    len(matches)
                )


            # -------------------------------------------------
            # CLIENT HISTORY
            # -------------------------------------------------

            st.subheader(
                "📋 Previous FP Encounters"
            )

            history_columns = [
                "encounter_id",
                "date",
                "method",
                "visit_type_for_method",
                "quantity_dispensed",
                "client_type"
            ]

            history = matches[
                history_columns
            ].copy()

            history = history.rename(
                columns={
                    "encounter_id": "Encounter ID",
                    "date": "Date",
                    "method": "Method",
                    "visit_type_for_method": "Visit Type",
                    "quantity_dispensed": "Quantity",
                    "client_type": "Client Type"
                }
            )

            display_styled_table(history)


            # -------------------------------------------------
            # NEW ENCOUNTER
            # -------------------------------------------------

            if can_edit_clients:

                st.divider()

                st.subheader(
                    "➕ Record New Encounter"
                )

                st.info(
                    f"New encounter will remain linked "
                    f"to Client ID: {selected_client_id}"
                )

                with st.form(
                    "existing_client_encounter_form"
                ):

                    st.markdown(
                        "**Encounter Information**"
                    )

                    form_col1, form_col2 = st.columns(2)

                    with form_col1:

                        service_date = st.date_input(
                            "Service Date",
                            value=date.today()
                        )

                        sex = st.selectbox(
                            "Sex",
                            [
                                "Female",
                                "Male"
                            ],
                            index=(
                                0
                                if client["sex"] == "Female"
                                else 1
                            )
                        )

                        age = st.number_input(
                            "Age",
                            min_value=10,
                            max_value=100,
                            value=int(client["age"])
                        )

                        client_type = st.selectbox(
                            "Client Type",
                            [
                                "New",
                                "Revisit"
                            ],
                            index=1
                        )

                        first_ever_user = st.selectbox(
                            "First-Ever FP User",
                            [
                                "Yes",
                                "No"
                            ],
                            index=1
                        )

                    with form_col2:

                        method = st.selectbox(
                            "Family Planning Method",
                            [
                                "Male Condoms",
                                "Female Condoms",
                                "Combined Oral Contraceptive Pills",
                                "Progestin Only Pills",
                                "Emergency Contraception",
                                "DMPA-IM",
                                "DMPA-SC",
                                "Implant 1 Rod",
                                "Implant 2 Rods",
                                "IUCD",
                                "Other"
                            ]
                        )

                        visit_type = st.selectbox(
                            "Visit Type for Method",
                            [
                                "Initiation",
                                "Revisit",
                                "Check-up",
                                "Removal",
                                "Switching",
                                "Resupply"
                            ]
                        )

                        quantity = st.number_input(
                            "Quantity Dispensed",
                            min_value=0,
                            step=1,
                            value=1
                        )

                        referral = st.selectbox(
                            "Referral",
                            [
                                "None",
                                "Yes"
                            ]
                        )


                    st.markdown(
                        "**Counselling & Screening**"
                    )

                    c1, c2, c3 = st.columns(3)

                    with c1:

                        counsel_fp = st.selectbox(
                            "FP Counselling",
                            [
                                "Yes",
                                "No"
                            ]
                        )

                        counsel_hiv = st.selectbox(
                            "HIV Counselling",
                            [
                                "Yes",
                                "No"
                            ]
                        )

                    with c2:

                        hiv_tested = st.selectbox(
                            "HIV Tested",
                            [
                                "Yes",
                                "No"
                            ]
                        )

                        hiv_status = st.selectbox(
                            "HIV Status",
                            [
                                "Negative",
                                "Positive",
                                "Unknown"
                            ]
                        )

                    with c3:

                        tb_screening = st.selectbox(
                            "TB Screening",
                            [
                                "Yes",
                                "No"
                            ]
                        )

                        cervical_screening = st.selectbox(
                            "Cervical Cancer Screening",
                            [
                                "Normal",
                                "Not done",
                                "Abnormal"
                            ]
                        )


                    st.markdown(
                        "**PPFP Information**"
                    )

                    ppftiming = st.selectbox(
                        "PPFP Timing",
                        [
                            "Not applicable",
                            "Immediate post-partum",
                            "Within 48 hours",
                            "Within 6 weeks",
                            "Beyond 6 weeks"
                        ]
                    )


                    submitted = st.form_submit_button(
                        "💾 Save New Encounter",
                        use_container_width=True
                    )


                # ---------------------------------------------
                # SAVE EXISTING CLIENT ENCOUNTER
                # ---------------------------------------------

                if submitted:

                    current_df = load_data()

                    new_encounter_id = (
                        generate_next_encounter_id(
                            current_df
                        )
                    )

                    new_record = {
                        "client_id":
                            selected_client_id,

                        "encounter_id":
                            new_encounter_id,

                        "date":
                            service_date.strftime(
                                "%Y-%m-%d"
                            ),

                        "month":
                            service_date.strftime(
                                "%Y-%m"
                            ),

                        "sex":
                            sex,

                        "age":
                            age,

                        "client_type":
                            client_type,

                        "first_ever_user":
                            first_ever_user,

                        "method":
                            method,

                        "visit_type_for_method":
                            visit_type,

                        "quantity_dispensed":
                            quantity,

                        "client_count":
                            1,

                        "counselled_for_fp":
                            counsel_fp,

                        "counselled_for_hiv":
                            counsel_hiv,

                        "hiv_tested":
                            hiv_tested,

                        "hiv_status":
                            hiv_status,

                        "ppfp_timing":
                            ppftiming,

                        "tb_screening":
                            tb_screening,

                        "cervical_cancer_screening":
                            cervical_screening,

                        "referral":
                            referral
                    }

                    updated_df = pd.concat(
                        [
                            current_df,
                            pd.DataFrame(
                                [new_record]
                            )
                        ],
                        ignore_index=True
                    )

                    save_data(
                        updated_df
                    )

                    st.session_state.selected_client_id = (
                        selected_client_id
                    )

                    st.session_state.save_success_message = (
                        "New encounter saved successfully. "
                        f"Client ID: {selected_client_id} | "
                        f"Encounter ID: {new_encounter_id}"
                    )

                    st.rerun()


# =========================================================
# REGISTER NEW CLIENT
# =========================================================

elif workflow == "➕ Register New Client":

    st.subheader(
        "➕ Register New Client"
    )

    new_client_id = generate_next_client_id(
        df
    )

    st.markdown(
        f"""
        <div class="id-card">

        <div class="small-note">
        Generated Client ID
        </div>

        <div class="client-id">
        {new_client_id}
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "This Client ID will remain the same for future "
        "encounters with this client."
    )


    with st.form(
        "new_client_form"
    ):

        st.subheader(
            "Client Information"
        )

        col1, col2 = st.columns(2)

        with col1:

            service_date = st.date_input(
                "Service Date",
                value=date.today()
            )

            sex = st.selectbox(
                "Sex",
                [
                    "Female",
                    "Male"
                ]
            )

            age = st.number_input(
                "Age",
                min_value=10,
                max_value=100,
                value=25
            )

            first_ever_user = st.selectbox(
                "First-Ever FP User",
                [
                    "Yes",
                    "No"
                ],
                index=0
            )

        with col2:

            client_type = st.selectbox(
                "Client Type",
                [
                    "New",
                    "Revisit"
                ],
                index=0
            )

            method = st.selectbox(
                "Family Planning Method",
                [
                    "Male Condoms",
                    "Female Condoms",
                    "Combined Oral Contraceptive Pills",
                    "Progestin Only Pills",
                    "Emergency Contraception",
                    "DMPA-IM",
                    "DMPA-SC",
                    "Implant 1 Rod",
                    "Implant 2 Rods",
                    "IUCD",
                    "Other"
                ]
            )

            visit_type = st.selectbox(
                "Visit Type for Method",
                [
                    "Initiation",
                    "Revisit",
                    "Check-up",
                    "Removal",
                    "Switching",
                    "Resupply"
                ]
            )

            quantity = st.number_input(
                "Quantity Dispensed",
                min_value=0,
                step=1,
                value=1
            )


        st.subheader(
            "Counselling & Screening"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            counsel_fp = st.selectbox(
                "FP Counselling",
                [
                    "Yes",
                    "No"
                ]
            )

            counsel_hiv = st.selectbox(
                "HIV Counselling",
                [
                    "Yes",
                    "No"
                ]
            )

        with c2:

            hiv_tested = st.selectbox(
                "HIV Tested",
                [
                    "Yes",
                    "No"
                ]
            )

            hiv_status = st.selectbox(
                "HIV Status",
                [
                    "Negative",
                    "Positive",
                    "Unknown"
                ]
            )

        with c3:

            tb_screening = st.selectbox(
                "TB Screening",
                [
                    "Yes",
                    "No"
                ]
            )

            cervical_screening = st.selectbox(
                "Cervical Cancer Screening",
                [
                    "Normal",
                    "Not done",
                    "Abnormal"
                ]
            )


        st.subheader(
            "PPFP & Referral"
        )

        p1, p2 = st.columns(2)

        with p1:

            ppftiming = st.selectbox(
                "PPFP Timing",
                [
                    "Not applicable",
                    "Immediate post-partum",
                    "Within 48 hours",
                    "Within 6 weeks",
                    "Beyond 6 weeks"
                ]
            )

        with p2:

            referral = st.selectbox(
                "Referral",
                [
                    "None",
                    "Yes"
                ]
            )


        submitted = st.form_submit_button(
            "💾 Register Client & Save Encounter",
            use_container_width=True
        )


    if submitted:

        current_df = load_data()

        new_client_id = generate_next_client_id(
            current_df
        )

        new_encounter_id = generate_next_encounter_id(
            current_df
        )

        new_record = {
            "client_id":
                new_client_id,

            "encounter_id":
                new_encounter_id,

            "date":
                service_date.strftime(
                    "%Y-%m-%d"
                ),

            "month":
                service_date.strftime(
                    "%Y-%m"
                ),

            "sex":
                sex,

            "age":
                age,

            "client_type":
                client_type,

            "first_ever_user":
                first_ever_user,

            "method":
                method,

            "visit_type_for_method":
                visit_type,

            "quantity_dispensed":
                quantity,

            "client_count":
                1,

            "counselled_for_fp":
                counsel_fp,

            "counselled_for_hiv":
                counsel_hiv,

            "hiv_tested":
                hiv_tested,

            "hiv_status":
                hiv_status,

            "ppfp_timing":
                ppftiming,

            "tb_screening":
                tb_screening,

            "cervical_cancer_screening":
                cervical_screening,

            "referral":
                referral
        }

        updated_df = pd.concat(
            [
                current_df,
                pd.DataFrame(
                    [new_record]
                )
            ],
            ignore_index=True
        )

        save_data(
            updated_df
        )

        st.session_state.save_success_message = (
            "Client registered and encounter saved successfully. "
            f"Client ID: {new_client_id} | "
            f"Encounter ID: {new_encounter_id}"
        )

        st.rerun()


# =========================================================
# RECENT ENCOUNTERS
# =========================================================

st.divider()

st.subheader(
    "📋 Recent Service Encounters"
)

latest_df = load_data()

if not latest_df.empty:

    display_columns = [
        "client_id",
        "encounter_id",
        "date",
        "sex",
        "age",
        "client_type",
        "method",
        "visit_type_for_method",
        "quantity_dispensed"
    ]

    recent_records = latest_df[
        display_columns
    ].tail(10).copy()

    recent_records = recent_records.rename(
        columns={
            "client_id": "Client ID",
            "encounter_id": "Encounter ID",
            "date": "Date",
            "sex": "Sex",
            "age": "Age",
            "client_type": "Client Type",
            "method": "Method",
            "visit_type_for_method": "Visit Type",
            "quantity_dispensed": "Quantity"
        }
    )

    display_styled_table(recent_records)

else:

    st.info(
        "No service encounters have been recorded yet."
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Family Planning Management System | "
    "Njoro Sub-County Hospital"
)

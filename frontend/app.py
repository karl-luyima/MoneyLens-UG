
"""Main Streamlit application for MoneyLens UG."""

from decimal import Decimal
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from api_client import APIClient, APIError

st.set_page_config(
    page_title="MoneyLens UG",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# Application styling
# ---------------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F5F7FA;
    }

    [data-testid="stSidebar"] {
        background-color: #123B5D;
    }

    [data-testid="stSidebar"] * {
        color: white;
    }

    .main-title {
        color: #123B5D;
        font-size: 2rem;
        font-weight: 700;
    }

    .subtitle {
        color: #64748B;
        font-size: 0.95rem;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        min-height: 120px;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.95rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Session state and API client
# ---------------------------------------------------------

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None


def get_api_client() -> APIClient:
    """Create an API client using the current session token."""

    return APIClient(
        access_token=st.session_state.access_token,
    )


def logout() -> None:
    """Clear authentication information."""

    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_email = None
    st.rerun()


def format_currency(value: Any) -> str:
    """Format a numeric value as Ugandan shillings."""

    amount = Decimal(str(value or 0))
    return f"UGX {amount:,.0f}"


def show_error(error: Exception) -> None:
    """Display a user-friendly error message."""

    st.error(str(error))


# ---------------------------------------------------------
# Authentication
# ---------------------------------------------------------

def authentication_page() -> None:
    """Display registration and login forms."""

    st.markdown(
        '<p class="main-title">MoneyLens UG</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<p class="subtitle">Understand your mobile money. '
        'Take control of your finances.</p>',
        unsafe_allow_html=True,
    )

    st.divider()

    login_tab, register_tab = st.tabs(
        ["Login", "Create Account"]
    )

    with login_tab:
        st.subheader("Welcome back")

        with st.form("login_form"):
            email = st.text_input(
                "Email address",
                placeholder="you@example.com",
            )

            password = st.text_input(
                "Password",
                type="password",
            )

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True,
            )

            if submitted:
                if not email or not password:
                    st.warning("Please enter your email and password.")
                else:
                    try:
                        result = APIClient().login(email, password)

                        st.session_state.access_token = result[
                            "access_token"
                        ]
                        st.session_state.refresh_token = result[
                            "refresh_token"
                        ]
                        st.session_state.user_email = email

                        st.success("Login successful.")
                        st.rerun()

                    except APIError as exc:
                        show_error(exc)

    with register_tab:
        st.subheader("Create your MoneyLens account")

        with st.form("register_form"):
            new_email = st.text_input(
                "Email address",
                key="register_email",
                placeholder="you@example.com",
            )

            new_password = st.text_input(
                "Password",
                type="password",
                key="register_password",
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password",
            )

            submitted = st.form_submit_button(
                "Create Account",
                use_container_width=True,
            )

            if submitted:
                if not new_email or not new_password:
                    st.warning("Please complete all fields.")

                elif new_password != confirm_password:
                    st.error("Passwords do not match.")

                elif len(new_password) < 8:
                    st.error(
                        "Password must contain at least 8 characters."
                    )

                else:
                    try:
                        APIClient().register(
                            email=new_email,
                            password=new_password,
                        )

                        st.success(
                            "Account created successfully. "
                            "You can now log in."
                        )

                    except APIError as exc:
                        show_error(exc)


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------

def dashboard_page(client: APIClient) -> None:
    """Display financial insights and polished interactive charts."""

    st.title("Financial Dashboard")
    st.caption(
        "An overview of your mobile money transactions and spending."
    )

    try:
        insights = client.get_insights()
    except APIError as exc:
        show_error(exc)
        return

    total_income = insights.get("total_income", 0)
    total_expenses = insights.get("total_expenses", 0)
    total_fees = insights.get("total_fees", 0)
    transaction_count = insights.get("transaction_count", 0)

    # Financial KPI cards.
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Income", format_currency(total_income))
    col2.metric("Total Expenses", format_currency(total_expenses))
    col3.metric("Total Fees", format_currency(total_fees))
    col4.metric("Transactions", f"{transaction_count:,}")

    st.divider()

    # Monthly income and expense trend.
    st.subheader("Monthly Financial Trend")
    monthly_data = insights.get("monthly_trend", [])

    if monthly_data:
        trend_df = pd.DataFrame(monthly_data)
        trend_df["income"] = pd.to_numeric(
            trend_df["income"], errors="coerce"
        ).fillna(0)
        trend_df["expenses"] = pd.to_numeric(
            trend_df["expenses"], errors="coerce"
        ).fillna(0)

        # Sort month labels chronologically where they use YYYY-MM.
        trend_df["_month_sort"] = pd.to_datetime(
            trend_df["month"], format="%Y-%m", errors="coerce"
        )
        trend_df = trend_df.sort_values(
            "_month_sort", na_position="last"
        )

        monthly_chart = go.Figure()
        monthly_chart.add_trace(
            go.Scatter(
                x=trend_df["month"],
                y=trend_df["income"],
                name="Income",
                mode="lines+markers",
                line={"color": "#008C95", "width": 3},
                marker={"size": 8},
                hovertemplate=(
                    "<b>%{x}</b><br>Income: UGX %{y:,.0f}<extra></extra>"
                ),
            )
        )
        monthly_chart.add_trace(
            go.Scatter(
                x=trend_df["month"],
                y=trend_df["expenses"],
                name="Expenses",
                mode="lines+markers",
                line={"color": "#1976A8", "width": 3},
                marker={"size": 8},
                hovertemplate=(
                    "<b>%{x}</b><br>Expenses: UGX %{y:,.0f}<extra></extra>"
                ),
            )
        )
        monthly_chart.update_layout(
            height=350,
            margin={"l": 15, "r": 20, "t": 25, "b": 15},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
            font={"color": "#123B5D"},
            hovermode="x unified",
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
            xaxis={
                "title": None,
                "showgrid": False,
                "showline": True,
                "linecolor": "#E2E8F0",
            },
            yaxis={
                "title": "Amount (UGX)",
                "tickformat": ",.0f",
                "gridcolor": "#E2E8F0",
                "zeroline": False,
            },
        )
        st.plotly_chart(
            monthly_chart, use_container_width=True,
            config={"displayModeBar": False},
        )
    else:
        st.info("No monthly transaction data available yet.")

    st.divider()

    # Category and counterparty charts.
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Transaction Value by Category")
        category_data = insights.get("category_breakdown", [])

        if category_data:
            category_df = pd.DataFrame(category_data)
            category_df["total_amount"] = pd.to_numeric(
                category_df["total_amount"], errors="coerce"
            ).fillna(0)
            category_df = category_df.sort_values(
                "total_amount", ascending=True
            )

            category_chart = go.Figure(
                go.Bar(
                    x=category_df["total_amount"],
                    y=category_df["category"],
                    orientation="h",
                    marker={"color": "#008C95"},
                    text=[
                        f"UGX {amount:,.0f}"
                        for amount in category_df["total_amount"]
                    ],
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate=(
                        "<b>%{y}</b><br>Amount: UGX %{x:,.0f}"
                        "<extra></extra>"
                    ),
                )
            )
            category_chart.update_layout(
                height=max(300, 55 * len(category_df)),
                margin={"l": 10, "r": 35, "t": 15, "b": 35},
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="white",
                font={"color": "#123B5D"},
                showlegend=False,
                xaxis={
                    "title": "Amount (UGX)",
                    "tickformat": ",.0f",
                    "gridcolor": "#E2E8F0",
                    "zeroline": False,
                },
                yaxis={"title": None, "showgrid": False},
            )
            st.plotly_chart(
                category_chart, use_container_width=True,
                config={"displayModeBar": False},
            )
        else:
            st.info("No category information available yet.")

    with right_col:
        st.subheader("Top Counterparties")
        counterparty_data = insights.get("top_counterparties", [])

        if counterparty_data:
            counterparty_df = pd.DataFrame(counterparty_data)
            counterparty_df["total_amount"] = pd.to_numeric(
                counterparty_df["total_amount"], errors="coerce"
            ).fillna(0)
            counterparty_df = counterparty_df.sort_values(
                "total_amount", ascending=True
            )

            counterparty_chart = go.Figure(
                go.Bar(
                    x=counterparty_df["total_amount"],
                    y=counterparty_df["counterparty"],
                    orientation="h",
                    marker={"color": "#1976A8"},
                    text=[
                        f"UGX {amount:,.0f}"
                        for amount in counterparty_df["total_amount"]
                    ],
                    textposition="outside",
                    cliponaxis=False,
                    hovertemplate=(
                        "<b>%{y}</b><br>Amount: UGX %{x:,.0f}"
                        "<extra></extra>"
                    ),
                )
            )
            counterparty_chart.update_layout(
                height=max(300, 55 * len(counterparty_df)),
                margin={"l": 10, "r": 35, "t": 15, "b": 35},
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="white",
                font={"color": "#123B5D"},
                showlegend=False,
                xaxis={
                    "title": "Amount (UGX)",
                    "tickformat": ",.0f",
                    "gridcolor": "#E2E8F0",
                    "zeroline": False,
                },
                yaxis={"title": None, "showgrid": False},
            )
            st.plotly_chart(
                counterparty_chart, use_container_width=True,
                config={"displayModeBar": False},
            )
        else:
            st.info("No counterparty information available yet.")

    st.divider()

    # Anomaly detection.
    st.subheader("Unusual Transactions")
    anomalies = insights.get("anomalies", [])

    if anomalies:
        anomaly_df = pd.DataFrame(anomalies).copy()
        if "amount" in anomaly_df.columns:
            anomaly_df["amount"] = anomaly_df["amount"].map(
                format_currency
            )
        st.warning(
            f"{len(anomalies)} unusual transaction(s) detected."
        )
        st.dataframe(
            anomaly_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("No unusual transactions detected.")


# ---------------------------------------------------------
# Upload page
# ---------------------------------------------------------

def upload_page(client: APIClient) -> None:
    """Allow users to upload SMS messages and files."""

    st.title("Upload Transactions")

    st.caption(
        "Import your mobile money messages to analyse your finances."
    )

    sms_tab, file_tab = st.tabs(
        ["Paste SMS Messages", "Upload TXT / CSV"]
    )

    with sms_tab:
        st.subheader("Paste mobile money messages")

        messages_text = st.text_area(
            "Enter your messages",
            height=250,
            placeholder=(
                "You have sent UGX 35,000 to John...\n"
                "You have received UGX 50,000 from Mary..."
            ),
        )

        if st.button(
            "Process Messages",
            type="primary",
            key="process_messages",
        ):
            messages = [
                message.strip()
                for message in messages_text.splitlines()
                if message.strip()
            ]

            if not messages:
                st.warning("Please enter at least one message.")

            else:
                with st.spinner("Processing your messages..."):
                    try:
                        result = client.upload_messages(messages)

                        st.success("Messages processed successfully.")

                        col1, col2, col3, col4 = st.columns(4)

                        col1.metric(
                            "Total",
                            result.get("total_messages", 0),
                        )

                        col2.metric(
                            "Parsed",
                            result.get("parsed_count", 0),
                        )

                        col3.metric(
                            "Duplicates",
                            result.get("duplicate_count", 0),
                        )

                        col4.metric(
                            "Unparsed",
                            result.get("unparsed_count", 0),
                        )

                    except APIError as exc:
                        show_error(exc)

    with file_tab:
        st.subheader("Upload a transaction file")

        uploaded_file = st.file_uploader(
            "Choose a TXT or CSV file",
            type=["txt", "csv"],
            help="Maximum file size: 5 MB.",
        )

        if uploaded_file is not None:
            st.caption(f"Selected file: {uploaded_file.name}")

            if st.button(
                "Upload and Process File",
                type="primary",
                key="process_file",
            ):
                with st.spinner("Uploading and processing file..."):
                    try:
                        result = client.upload_file(
                            file_name=uploaded_file.name,
                            file_bytes=uploaded_file.getvalue(),
                        )

                        st.success("File processed successfully.")

                        col1, col2, col3, col4 = st.columns(4)

                        col1.metric(
                            "Total",
                            result.get("total_messages", 0),
                        )

                        col2.metric(
                            "Parsed",
                            result.get("parsed_count", 0),
                        )

                        col3.metric(
                            "Duplicates",
                            result.get("duplicate_count", 0),
                        )

                        col4.metric(
                            "Unparsed",
                            result.get("unparsed_count", 0),
                        )

                    except APIError as exc:
                        show_error(exc)


# ---------------------------------------------------------
# Transactions page
# ---------------------------------------------------------

def transactions_page(client: APIClient) -> None:
    """Display, filter and correct transaction categories."""

    st.title("Transactions")

    st.caption(
        "Review your transactions and correct their categories."
    )

    st.subheader("Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        provider = st.selectbox(
            "Provider",
            ["All", "MTN", "Airtel"],
        )

    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["timestamp", "amount", "created_at"],
        )

    with col3:
        sort_order = st.selectbox(
            "Sort order",
            ["desc", "asc"],
        )

    col4, col5 = st.columns(2)

    with col4:
        date_from = st.date_input(
            "From date",
            value=None,
        )

    with col5:
        date_to = st.date_input(
            "To date",
            value=None,
        )

    col6, col7 = st.columns(2)

    with col6:
        min_amount = st.number_input(
            "Minimum amount (UGX)",
            min_value=0.0,
            value=0.0,
        )

    with col7:
        max_amount = st.number_input(
            "Maximum amount (UGX)",
            min_value=0.0,
            value=0.0,
            help="Leave at zero for no maximum.",
        )

    page_size = st.selectbox(
        "Transactions per page",
        [10, 20, 50, 100],
        index=1,
    )

    page = st.number_input(
        "Page",
        min_value=1,
        value=1,
        step=1,
    )

    filters: dict[str, Any] = {
        "sort_by": sort_by,
        "sort_order": sort_order,
    }

    if provider != "All":
        filters["provider"] = provider.lower()

    if date_from:
        filters["date_from"] = date_from.isoformat()

    if date_to:
        filters["date_to"] = date_to.isoformat()

    if min_amount > 0:
        filters["min_amount"] = min_amount

    if max_amount > 0:
        filters["max_amount"] = max_amount

    if date_from and date_to and date_from > date_to:
        st.error("The start date cannot be after the end date.")
        return

    try:
        # Retrieve categories to translate category IDs into names.
        categories = client.get_categories()

        category_names = {
            category["id"]: category["name"]
            for category in categories
        }

        result = client.get_transactions(
            page=int(page),
            page_size=page_size,
            **filters,
        )

        transactions = result.get("items", [])

        st.write(
            f"Total transactions: {result.get('total', 0):,}"
        )

        if not transactions:
            st.info("No transactions found for these filters.")
            return

        # Display transaction records with category names.
        display_data = []

        for transaction in transactions:
            category_id = transaction["category_id"]

            category_name = (
                category_names.get(category_id, "Unknown Category")
                if category_id is not None
                else "Uncategorized"
            )

            display_data.append(
                {
                    "ID": transaction["id"],
                    "Date": transaction["timestamp"],
                    "Provider": transaction["provider"],
                    "Type": transaction["transaction_type"],
                    "Amount (UGX)": format_currency(
                        transaction["amount"]
                    ),
                    "Fee (UGX)": (
                        format_currency(transaction["fee"])
                        if transaction["fee"] is not None
                        else "UGX 0"
                    ),
                    "Counterparty": (
                        transaction["counterparty"] or "Unknown"
                    ),
                    "Category": category_name,
                }
            )

        st.dataframe(
            pd.DataFrame(display_data),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"Page {result.get('page', page)} of "
            f"{result.get('pages', 1)}"
        )

        st.divider()

        # Category correction.
        st.subheader("Correct Transaction Category")

        if not categories:
            st.warning("No categories are available.")
            return

        category_options = {
            category["name"]: category["id"]
            for category in categories
        }

        transaction_options = {
            (
                f"Transaction #{transaction['id']} — "
                f"{transaction['provider']} — "
                f"{format_currency(transaction['amount'])}"
            ): transaction["id"]
            for transaction in transactions
        }

        with st.form("category_correction_form"):
            selected_transaction = st.selectbox(
                "Select transaction",
                list(transaction_options.keys()),
            )

            selected_category = st.selectbox(
                "Select correct category",
                list(category_options.keys()),
            )

            submitted = st.form_submit_button(
                "Save Category Correction",
                type="primary",
            )

            if submitted:
                transaction_id = transaction_options[
                    selected_transaction
                ]

                category_id = category_options[
                    selected_category
                ]

                try:
                    client.update_transaction_category(
                        transaction_id=transaction_id,
                        category_id=category_id,
                    )

                    st.success(
                        "Transaction category updated successfully."
                    )
                    st.rerun()

                except APIError as exc:
                    show_error(exc)

    except APIError as exc:
        show_error(exc)


# ---------------------------------------------------------
# Upload history
# ---------------------------------------------------------

def upload_history_page(client: APIClient) -> None:
    """Display previous upload records."""

    st.title("Upload History")

    st.caption(
        "Review your previous mobile money imports."
    )

    try:
        result = client.get_uploads(
            page=1,
            page_size=50,
        )

        uploads = result.get("items", [])

        if not uploads:
            st.info("You have not uploaded any transactions yet.")
            return

        upload_data = []

        for upload in uploads:
            upload_data.append(
                {
                    "Upload ID": upload["id"],
                    "Source": upload["source_type"],
                    "Filename": upload["filename"] or "Pasted Messages",
                    "Total": upload["total_messages"],
                    "Parsed": upload["parsed_count"],
                    "Duplicates": upload["duplicate_count"],
                    "Unparsed": upload["unparsed_count"],
                    "Status": upload["status"],
                    "Date": upload["created_at"],
                }
            )

        st.dataframe(
            pd.DataFrame(upload_data),
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"Total upload records: {result.get('total', 0):,}"
        )

    except APIError as exc:
        show_error(exc)


# ---------------------------------------------------------
# Model management
# ---------------------------------------------------------

def model_page(client: APIClient) -> None:
    """Allow users to retrain their personalized category model."""

    st.title("Personalized Categorization")

    st.write(
        "MoneyLens can use your category corrections to improve "
        "personalized transaction categorization."
    )

    st.info(
        "Correct transaction categories first. Then retrain your "
        "personalized model using those corrections."
    )

    if st.button(
        "Retrain My Category Model",
        type="primary",
    ):
        with st.spinner("Training your personalized model..."):
            try:
                result = client.retrain_category_model()

                st.success(
                    result.get(
                        "message",
                        "Model trained successfully.",
                    )
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Model Version",
                    result.get("model_version", "N/A"),
                )

                col2.metric(
                    "Corrections Used",
                    result.get("corrections_used", 0),
                )

                col3.metric(
                    "Training Examples",
                    result.get("training_examples", 0),
                )

            except APIError as exc:
                show_error(exc)


# ---------------------------------------------------------
# Main application
# ---------------------------------------------------------

def main() -> None:
    """Run the MoneyLens UG application."""

    if not st.session_state.access_token:
        authentication_page()
        return

    client = get_api_client()

    with st.sidebar:
        st.title("MoneyLens UG")

        st.caption("Personal Finance Insights")

        st.divider()

        st.write(
            f"Logged in as: {st.session_state.user_email}"
        )

        selected_page = st.radio(
            "Navigation",
            [
                "Dashboard",
                "Upload Transactions",
                "Transactions",
                "Upload History",
                "Personalized Model",
            ],
        )

        st.divider()

        if st.button(
            "Logout",
            use_container_width=True,
        ):
            logout()

    if selected_page == "Dashboard":
        dashboard_page(client)

    elif selected_page == "Upload Transactions":
        upload_page(client)

    elif selected_page == "Transactions":
        transactions_page(client)

    elif selected_page == "Upload History":
        upload_history_page(client)

    elif selected_page == "Personalized Model":
        model_page(client)


if __name__ == "__main__":
    main()

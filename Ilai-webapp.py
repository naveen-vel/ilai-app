from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import streamlit as st
import gspread
from datetime import datetime

# OAuth scopes and redirect URL
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
REDIRECT_URI = "https://ilai-restaurant.streamlit.app"

# Load client ID and secret from Streamlit secrets
client_id = st.secrets["google_oauth"]["client_id"]
client_secret = st.secrets["google_oauth"]["client_secret"]

st.title("Employee Sign-In with Google Authentication")

if "credentials" not in st.session_state:
    st.session_state.credentials = None

# Handle OAuth callback
query_params = st.query_params
if st.session_state.credentials is None and "code" in query_params:
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": [REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=query_params["code"])
        credentials = flow.credentials

        st.session_state.credentials = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }

        st.query_params.clear()
        st.experimental_rerun()
    except Exception as e:
        st.error("Authentication failed. Please try again.")
        st.stop()

# If not logged in, show sign-in link
if st.session_state.credentials is None:
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": [REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, _ = flow.authorization_url(prompt="consent")
    st.write("Click below to sign in with Google:")
    st.write(f"[Sign in with Google]({auth_url})")

else:
    creds = Credentials(
        token=st.session_state.credentials["token"],
        refresh_token=st.session_state.credentials["refresh_token"],
        token_uri=st.session_state.credentials["token_uri"],
        client_id=st.session_state.credentials["client_id"],
        client_secret=st.session_state.credentials["client_secret"],
        scopes=st.session_state.credentials["scopes"],
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    st.success("Authenticated with Google!")

    client = gspread.authorize(creds)

    try:
        sheet = client.open("Employee Sign-In").sheet1
    except gspread.SpreadsheetNotFound:
        st.warning("Spreadsheet not found. Creating a new one...")
        spreadsheet = client.create("Employee Sign-In")
        spreadsheet.share("your-email@example.com", perm_type="user", role="writer")
        sheet = spreadsheet.sheet1
        st.success("New spreadsheet created successfully!")

    # Initialize session fields
    if "name_input" not in st.session_state:
        st.session_state.name_input = ""
    if "id_input" not in st.session_state:
        st.session_state.id_input = ""

    name = st.text_input("Enter your name", value=st.session_state.name_input, key="name_input")
    emp_id = st.text_input("Enter your ID", value=st.session_state.id_input, key="id_input")

    if st.button("Sign In"):
        if name and emp_id:
            sign_in_time = datetime.now().strftime("%I:%M %p, %b %d, %Y")
            try:
                sheet.append_row([name, emp_id, sign_in_time, "Sign In"])
                st.success(f"{name} signed in at {sign_in_time}")
                st.session_state.name_input = ""
                st.session_state.id_input = ""
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to save to Google Sheets: {e}")
        else:
            st.error("Please enter both your name and ID.")

    if st.button("Sign Out"):
        if name and emp_id:
            sign_out_time = datetime.now().strftime("%I:%M %p, %b %d, %Y")
            try:
                sheet.append_row([name, emp_id, sign_out_time, "Sign Out"])
                st.success(f"{name} signed out at {sign_out_time}")
                st.session_state.name_input = ""
                st.session_state.id_input = ""
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to save to Google Sheets: {e}")
        else:
            st.error("Please enter both your name and ID.")

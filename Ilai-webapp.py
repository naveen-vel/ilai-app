from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import streamlit as st
import gspread
from datetime import datetime

# OAuth scopes and redirect URL
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
REDIRECT_URI = "https://ilai-restaurant.streamlit.app"  # For deployment on Streamlit Cloud

# Load client ID and secret from Streamlit secrets
client_id = st.secrets["google_oauth"]["client_id"]
client_secret = st.secrets["google_oauth"]["client_secret"]

st.title("Employee Sign-In with Google Authentication")

if "credentials" not in st.session_state:
    st.session_state.credentials = None

if st.session_state.credentials is None:
    query_params = st.query_params
    if "code" in query_params:
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
        st.success("Google Sign-In successful!")
        if st.button("Continue to app"):
            st.query_params.clear()
            st.experimental_rerun()

    else:
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

    employee_name = st.text_input("Enter your name")
    employee_id = st.text_input("Enter your ID")

    if st.button("Sign In"):
        if employee_name and employee_id:
            sign_in_time = datetime.now().strftime("%I:%M %p, %b %d, %Y")
            st.success(f"Signed in successfully at {sign_in_time}")
            try:
                sheet.append_row([employee_name, employee_id, sign_in_time, "Sign In"])
                st.success("Sign-in details saved to Google Sheets.")
            except Exception as e:
                st.error(f"Failed to save to Google Sheets: {e}")
        else:
            st.error("Please enter both your name and ID.")

    if st.button("Sign Out"):
        if employee_name and employee_id:
            sign_out_time = datetime.now().strftime("%I:%M %p, %b %d, %Y")
            st.success(f"Signed out successfully at {sign_out_time}")
            try:
                sheet.append_row([employee_name, employee_id, sign_out_time, "Sign Out"])
                st.success("Sign-out details saved to Google Sheets.")
            except Exception as e:
                st.error(f"Failed to save to Google Sheets: {e}")
        else:
            st.error("Please enter both your name and ID.")

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import streamlit as st
import gspread
from datetime import datetime

# Google OAuth Configuration
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
# REDIRECT_URI = "http://localhost:8501/"  # For local testing or update for your deployed URL
REDIRECT_URI = "https://ilai-restaurant.streamlit.app"  # For local testing or update for your deployed URL

st.title("Employee Sign-In with Google Authentication")

if "credentials" not in st.session_state:
    st.session_state.credentials = None

if st.session_state.credentials is None:
    # Use st.query_params to get the authorization code
    query_params = st.query_params
    if "code" in query_params:
        # Exchange the authorization code for credentials
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
        )
        flow.fetch_token(code=query_params["code"])
        credentials = flow.credentials

        # Save credentials to session state
        st.session_state.credentials = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
        }
        st.success("Google Sign-In successful! You can now access the app.")

        # Clear the query parameters (remove the "code" from the URL)
        st.query_params.clear()
        st.experimental_rerun()

    else:
        # Generate OAuth URL and redirect the user
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(prompt="consent")
        st.write("Click below to sign in with Google:")
        st.write(f"[Sign in with Google]({auth_url})")
else:
    # Credentials exist in session state, continue with authentication
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
    # Initialize Google Sheets API
    client = gspread.authorize(creds)
    # Initialize Google Sheets API
    # client = gspread.authorize(creds)
    # sheet = client.open("Employee Sign-In").sheet1
    # Check if the spreadsheet exists; if not, create it
    try:
        sheet = client.open("Employee Sign-In").sheet1
    except gspread.SpreadsheetNotFound:
        st.warning("Spreadsheet not found. Creating a new one...")
        spreadsheet = client.create("Employee Sign-In")
        # Share the spreadsheet with the authenticated user's email (optional)
        spreadsheet.share("your-email@example.com", perm_type="user", role="writer")
        sheet = spreadsheet.sheet1
        st.success("New spreadsheet created successfully!")


    # Employee Sign-In Form
    employee_name = st.text_input("Enter your name")
    employee_id = st.text_input("Enter your ID")

    if st.button("Sign In"):
        if employee_name and employee_id:
            sign_in_time = datetime.now().strftime("%I:%M %p, %b %d, %Y")
            st.success(f"Signed in successfully at {sign_in_time}")

            # Save to Google Sheets
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

            # Save to Google Sheets
            try:
                sheet.append_row([employee_name, employee_id, sign_out_time, "Sign Out"])
                st.success("Sign-out details saved to Google Sheets.")
            except Exception as e:
                st.error(f"Failed to save to Google Sheets: {e}")
        else:
            st.error("Please enter both your name and ID.")
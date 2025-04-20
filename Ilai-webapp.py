from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import streamlit as st
import gspread
import pytz
from datetime import datetime
import requests

def send_telegram_alert(message):
    token = st.secrets["telegram"]["bot_token"]  # Access token from secrets.toml
    chat_id = st.secrets["telegram"]["chat_id"]  # Access chat_id from secrets.toml
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, data=payload)
    return response.json()

# Set your local timezone (e.g., 'Asia/Kolkata' or 'Europe/Berlin')
timezone = pytz.timezone('Europe/Berlin')  # Change this to your desired timezone

# Get current time with the timezone
# localized_time = datetime.now(timezone)


# OAuth scopes and redirect URL
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
REDIRECT_URI = "https://ilai-restaurant.streamlit.app"  # For deployment on Streamlit Cloud

# Load client ID and secret from Streamlit secrets
client_id = st.secrets["google_oauth"]["client_id"]
client_secret = st.secrets["google_oauth"]["client_secret"]

st.title("Employee Sign-In with Google Authentication")

if "credentials" not in st.session_state:
    st.session_state.credentials = None

query_params = st.query_params

# Authentication flow
if st.session_state.credentials is None:
    if "code" in query_params:
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
            st.rerun()
        except Exception:
            st.error("Authentication failed. Please try again.")
            st.stop()
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
        st.stop()

# After successful authentication, check if the app should show the 'Authenticated with Google' message
if "show_app" not in st.session_state:
    st.success("Authenticated with Google!")
    if st.button("Continue to App"):
        st.session_state.show_app = True
        st.rerun()
    st.stop()


# Credentials are available, so proceed with the app logic
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

client = gspread.authorize(creds)

try:
    sheet = client.open("Employee Sign-In").sheet1
except gspread.SpreadsheetNotFound:
    st.warning("Spreadsheet not found. Creating a new one...")
    spreadsheet = client.create("Employee Sign-In")
    spreadsheet.share("your-email@example.com", perm_type="user", role="writer")
    sheet = spreadsheet.sheet1
    st.success("New spreadsheet created successfully!")

# if "name_input" not in st.session_state:
#     st.session_state.name_input = ""
# if "id_input" not in st.session_state:
#     st.session_state.id_input = ""

employee_name = st.text_input("Enter your name", value=" ", key="name_input")
employee_id = st.text_input("Enter your ID", value=" ", key="id_input")

st.session_state.setdefault("name_input"," ")
st.session_state.setdefault("id_input"," ")

# Sign-In Logic
if st.button("Sign In"):
    if employee_name and employee_id:
        sign_in_time = datetime.now(timezone).strftime("%I:%M %p, %b %d, %Y")
        try:
            sheet.append_row([employee_name, employee_id, sign_in_time, "Sign In"])
            st.success(f"Signed in successfully at {sign_in_time}")
            send_telegram_alert(f"{employee_name} signed in at {sign_in_time}")
            # Reset the session state for inputs before rerun
            
            # st.session_state.name_input = " "  # Reset session state for name
            # st.session_state.id_input = " "    # Reset session state for ID

            # Trigger a rerun
            st.rerun()      

        except Exception as e:
            st.error(f"Failed to save to Google Sheets: {e}")
    else:
        st.error("Please enter both your name and ID.")

# Sign-Out Logic
if st.button("Sign Out"):
    if employee_name and employee_id:
        sign_out_time = datetime.now(timezone).strftime("%I:%M %p, %b %d, %Y")
        try:
            sheet.append_row([employee_name, employee_id, sign_out_time, "Sign Out"])
            st.success(f"Signed out successfully at {sign_out_time}")
            send_telegram_alert(f"{employee_name} signed out at {sign_out_time}")
            # Reset the session state for inputs before rerun
            
            # st.session_state.name_input = " "  # Reset session state for name
            # st.session_state.id_input = " "    # Reset session state for ID
            
            # Trigger a rerun
            st.rerun()

        except Exception as e:
            st.error(f"Failed to save to Google Sheets: {e}")
    else:
        st.error("Please enter both your name and ID.")

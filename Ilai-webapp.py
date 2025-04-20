from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import streamlit as st
import gspread
import pytz
import requests
import math
from datetime import datetime, timedelta
import time

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
client_id = st.secrets["google_oauth_ilai"]["client_id"]
client_secret = st.secrets["google_oauth_ilai"]["client_secret"]

st.set_page_config(page_title="Team Ilai", layout="centered")
st.markdown("""
    <h1 style='text-align: center; color: #4A4A4A;'>👩‍🍳 Team Ilai </h1>
    <h4 style='text-align: center; color: #777;'>Timesheet Management System</h4>
""", unsafe_allow_html=True)
# st.title("Team Ilai Timesheet Management")

if "credentials" not in st.session_state:
    st.session_state.credentials = None

query_params = st.query_params  # ✅ Correct way to access query parameters

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
            st.query_params.clear()  # This clears the query params
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
        st.info("🔐 Click below to sign in with your Google account:")
        st.markdown(f"[👉 Sign in with Google]({auth_url})")
        st.stop()

# After successful authentication, check if the app should show the 'Authenticated with Google' message
if "show_app" not in st.session_state:
    st.success("Authenticated with Google!")
    if st.button("✅ Continue to App"):
        st.session_state.show_app = True
        st.rerun()
    st.stop()

# if st.session_state.credentials["client_id"] != client_id:
#     # Client ID has changed — invalidate session
#     st.session_state.credentials = None
#     st.session_state.show_app = False
#     st.rerun()

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

# create or open sheet for current month
current_month = datetime.now().strftime("%B %Y")
spreadsheet_name = "Employee Sign-In"

try:
    spreadsheet = client.open(spreadsheet_name)
except gspread.SpreadsheetNotFound:
    spreadsheet = client.create(spreadsheet_name)
    spreadsheet.share("naveen.velmurugan@virgildynamics.com", perm_type="user", role="writer")

try:
    sheet = spreadsheet.worksheet(current_month)
except gspread.WorksheetNotFound:
    sheet = spreadsheet.add_worksheet(title=current_month, rows="1000", cols="10")
    sheet.update("A1:H1", [["Name", "Date", "Check In", "Check Out", "Break Start", "Break End", "Hours Worked", "Week"]])

employee_list = ["",
                 "Naveen Ballapuri",
                 "Sai Harshita Bandhar Suresh",
                 "Urekha Nuthapalati",
                 "Varaha Shivakumar"]

if "name_input" not in st.session_state:
    st.session_state.name_input = employee_list[0]

st.markdown("---")
employee_name = st.selectbox("👤 Select your name", employee_list, index=0, key="name_input")

if not employee_name:
    st.stop()

records = sheet.get_all_records()
today_str = datetime.now().strftime("%Y-%m-%d")
latest_entry = next((row for row in reversed(records) if row['Name'] == employee_name and row['Date'] == today_str), None)

now = datetime.now()
current_date = now.strftime("%Y-%m-%d")
current_time = now.strftime("%H:%M:%S")
current_week = now.isocalendar()[1]

st.markdown("---")
st.markdown("<h3 style='color: #4a90e2;'>⏱️ Actions</h3>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

if "status_message" not in st.session_state:
    st.session_state.status_message = ""
    st.session_state.message_timestamp = None

with col1:
    if st.button("📥 Check In"):
        if latest_entry is None:
            sheet.append_row([employee_name, current_date, current_time, '', '', '', '', current_week])
            st.session_state.status_message = f"✅ Checked in at {current_time}"
            st.session_state.message_timestamp = time.time()
            send_telegram_alert(f"{employee_name} checked in at {current_time}")
            st.rerun()
        else:
            st.session_state.status_message = "⚠️ You have already checked in today."
            st.session_state.message_timestamp = time.time()

with col2:
    if st.button("📤 Check Out"):
        if latest_entry:
            if latest_entry['Check Out']:
                st.session_state.status_message = "⚠️ You have already checked out."
                st.session_state.message_timestamp = time.time()
                # st.rerun()
            elif latest_entry['Break Start'] and not latest_entry['Break End']:
                row_index = records.index(latest_entry) + 2
                sheet.update_cell(row_index, 4, current_time)
                sheet.update_cell(row_index, 6, current_time)

                checkin_time = datetime.strptime(latest_entry['Check In'], "%H:%M:%S")
                checkout_time = datetime.strptime(current_time, "%H:%M:%S")

                break_start = datetime.strptime(latest_entry['Break Start'], "%H:%M:%S") if latest_entry['Break Start'] else None
                break_end = datetime.strptime(latest_entry['Break End'], "%H:%M:%S") if latest_entry['Break End'] else None

                break_duration = (break_end - break_start).total_seconds() if break_start and break_end else 0
                total_duration = (checkout_time - checkin_time).total_seconds() - break_duration
                total_hours = round(total_duration / 3600, 2)

                sheet.update_cell(row_index, 7, total_hours)
                st.session_state.status_message = f"✅ Checked out at {current_time}. Total hours: {total_hours}"
                st.session_state.message_timestamp = time.time()
                send_telegram_alert(f"{employee_name} checked out at {current_time} and spent {total_hours} hours today")
                st.rerun()
            else:
                row_index = records.index(latest_entry) + 2
                sheet.update_cell(row_index, 4, current_time)

                checkin_time = datetime.strptime(latest_entry['Check In'], "%H:%M:%S")
                checkout_time = datetime.strptime(current_time, "%H:%M:%S")

                break_start = datetime.strptime(latest_entry['Break Start'], "%H:%M:%S") if latest_entry['Break Start'] else None
                break_end = datetime.strptime(latest_entry['Break End'], "%H:%M:%S") if latest_entry['Break End'] else None

                break_duration = (break_end - break_start).total_seconds() if break_start and break_end else 0
                total_duration = (checkout_time - checkin_time).total_seconds() - break_duration
                total_hours = round(total_duration / 3600, 2)

                sheet.update_cell(row_index, 7, total_hours)
                st.session_state.status_message = f"✅ Checked out at {current_time}. Total hours: {total_hours}"
                st.session_state.message_timestamp = time.time()
                send_telegram_alert(f"{employee_name} checked out at {current_time} and spent {total_hours} hours today")
                st.rerun()
        else:
            st.session_state.status_message = "⚠️ No check-in record found for today."
            st.session_state.message_timestamp = time.time()
            # st.rerun()

with col3:
    if st.button("☕ Break Start"):
        if latest_entry:
            if latest_entry['Break Start']:
                st.session_state.status_message = "⚠️ Break already started."
                st.session_state.message_timestamp = time.time()
                # st.rerun()
            elif latest_entry['Check Out']:
                st.session_state.status_message = "⚠️ Cannot start break after checking out."
                st.session_state.message_timestamp = time.time()
                # st.rerun()
            else:
                row_index = records.index(latest_entry) + 2
                sheet.update_cell(row_index, 5, current_time)
                st.session_state.status_message = f"✅ Break started at {current_time}"
                st.session_state.message_timestamp = time.time()
                send_telegram_alert(f"{employee_name} started break at {current_time}")
                st.rerun()
        else:
            st.session_state.status_message = "⚠️ No check-in record found for today."
            st.session_state.message_timestamp = time.time()
            # st.rerun()

with col4:
    if st.button("🔚 Break End"):
        if latest_entry:
            if latest_entry['Check Out']:
                st.session_state.status_message = "⚠️ Cannot end break after checking out."
                st.session_state.message_timestamp = time.time()
                # st.rerun()
            elif not latest_entry['Break Start']:
                st.session_state.status_message = "⚠️ Break not started yet."
                st.session_state.message_timestamp = time.time()
                # st.rerun()
            elif latest_entry['Break End']:
                st.session_state.status_message = "⚠️ Break already ended."
                st.session_state.message_timestamp = time.time()
                # st.rerun()
            else:
                break_start_time = datetime.strptime(latest_entry['Break Start'], "%H:%M:%S")
                if datetime.strptime(current_time, "%H:%M:%S") < break_start_time:
                    st.session_state.status_message = "⚠️ Break end time must be after break start time."
                    st.session_state.message_timestamp = time.time()
                    # st.rerun()
                else:
                    row_index = records.index(latest_entry) + 2
                    sheet.update_cell(row_index, 6, current_time)
                    st.session_state.status_message = f"✅ Break ended at {current_time}"
                    st.session_state.message_timestamp = time.time()
                    send_telegram_alert(f"{employee_name} finished break at {current_time}")
                    st.rerun()
        else:
            st.session_state.status_message = "⚠️ No check-in record found for today."
            st.session_state.message_timestamp = time.time()
            # st.rerun()

if st.session_state.status_message:
    if st.session_state.message_timestamp and time.time() - st.session_state.message_timestamp < 10:
        st.markdown("---")
        st.success(st.session_state.status_message)
        # st.rerun()
    else:
        st.session_state.status_message = ""
        st.session_state.message_timestamp = None
        # st.rerun()
import streamlit as st
import requests
from datetime import timedelta
import gspread
from google.oauth2.service_account import Credentials
import json

# Initialize headers and URL for Algolia authentication
if 'headers' not in st.session_state:
    st.session_state.headers = {
    "x-algolia-application-id": st.secrets["ALGOLIA_CREDENTIALS"]["application_id"],
    "x-algolia-api-key": st.secrets["ALGOLIA_CREDENTIALS"]["api_key"],
    "Content-Type": "application/json"
    }
    st.session_state.url = st.secrets["ALGOLIA_CREDENTIALS"]["endpoint"]

# Initialize session state for selected songs if not already initialized
if 'selected_songs' not in st.session_state:
    st.session_state.selected_songs = []

# Initialize session state for search results if not already initialized
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# Initialize session state for deleted songs
if 'deleted' not in st.session_state:
    st.session_state.deleted = False
elif st.session_state.deleted is True:
    st.toast("Song removed", icon="😔")
    st.session_state.deleted = False

if 'sheet_id' not in st.session_state:
    st.session_state.sheet_id = st.secrets["GOOGLE_CREDENTIALS"]["sheet_id"]

# Function to create a client
def create_client():
    # Check if 'client' exists in session_state, if not, create it
    if "client" not in st.session_state:
        # Define the scopes required for your Google Sheets API
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        google_credentials = st.secrets["GOOGLE_CREDENTIALS"]["value"]
        credentials_dict = json.loads(google_credentials)

        # Create credentials from the loaded dictionary
        creds = Credentials.from_service_account_info(credentials_dict, scopes=scopes)

        # Authorize the client and store it in session_state
        st.session_state.client = gspread.authorize(creds)
        st.toast("Client created")

    return st.session_state.client

# Function to fetch the sheet
def fetch_sheet():
    client = create_client()  # Ensure client is created
    sheet = client.open_by_key(st.session_state.sheet_id).sheet1
    return sheet

# Function to save to Google Sheets
def save_to_google_sheets():
    # Open the Google Sheet
    sheet = fetch_sheet()  # Replace with your sheet name
    
    # Clear existing data (optional)
    sheet.clear()
    sheet.append_row(["selected_song"])

    # Ensure each song is in its own row (Google Sheets expects a list of lists)
    formatted_songs = [[song] for song in st.session_state.selected_songs]  # Convert to list of lists
    sheet.update("A2", formatted_songs)  # Writes from cell A1 downwards

    # for song in st.session_state.selected_songs:
    #    sheet.append_row([song])  # Ensure `song` is a list (e.g., [artist, title, length])

def standardize_length(length):
    # Handle None or empty values
    if length is None or length == '':
        return "00:00"
    
    # Handle "0:00:00" format (extract MM:SS)
    if len(length.split(':')) == 3:
        _, mm, ss = length.split(':')
        return f"{mm.zfill(2)}:{ss.zfill(2)}"
    
    # Handle "0:00" or "3:18" format (ensure two digits)
    if len(length.split(':')) == 2:
        mm, ss = length.split(':')
        return f"{mm.zfill(2)}:{ss.zfill(2)}"
    
    # Default fallback
    return "00:00"

# Streamlit UI
st.title("Tune Timer")

# Textbox for query input
query = st.text_input("", placeholder="Enter song or artist name")

col1, col2 = st.columns([4, 1])

# Button to trigger search
with col2:
    if st.button("Search", type="primary") or query:
        # Search query payload
        payload = {
            "requests": [
                {
                    "indexName": "songs",  # Replace with actual index name
                    "params": f"query={query}"
                }
            ]
        }

        # Making the request
        response = requests.post(st.session_state.url, json=payload, headers=st.session_state.headers)

        # Checking the response
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results'][0]['hits']) > 0:
                # Store search results in session state
                st.session_state.search_results = data['results'][0]['hits']
                with col1:
                    st.subheader("Search results")
            else:
                st.session_state.search_results = []
                with col1:
                    st.write("No results found")
        else:
            with col1:
                st.write(f"Request failed: {response.status_code}, {response.text}")

# Display search results and handle song selection
if st.session_state.search_results:
    st.write("Click to select song")
    for i, hit in enumerate(st.session_state.search_results):

        # Standardize the length field
        try:
            hit['length'] = standardize_length(hit['length'])
        except:
            hit['length'] = "00:00"
        
        song = f"{hit['artistITSO']} - {hit['title']} [{hit['length']}]"
        
        # Display a button for each song with a unique key
        if st.button(f"{song}", key=f"select_{i}"):
            # Add selected song to session state
            if song not in st.session_state.selected_songs:
                st.session_state.selected_songs.append(song)
                sheet = fetch_sheet()
                sheet.append_row([song])
                st.toast("Song added", icon="🎉")
            else:
                st.toast("Song already added", icon="👍")

# Display selected songs with a remove button for each
st.divider()
col1, col2 = st.columns([4, 1])
with col1:
    st.subheader("Selected Songs")

'''
# Save to sheets when the list changes
with col2:
    if st.button("Save", key=f"save"):
        save_to_google_sheets()
        values = fetch_sheet()
        # st.write(values.get_all_records())
        st.toast("Selected songs saved!")
'''

'''
    # Load songs
    values = fetch_sheet()
    st.write(values.get_all_records())
'''

if st.session_state.selected_songs:

    # Calculate total length of selected songs
    total_length_seconds = 0
    for song in st.session_state.selected_songs:
        # Extract the length from the song string (assuming format "Length: MM:SS")
        time_start = song.find("[") + 1  # Find the index of "(" and move 1 character ahead
        time_end = song.find("]")        # Find the index of ")"
        length_str = song[time_start:time_end] # Slice the string to get the time
        minutes, seconds = map(int, length_str.split(":"))
        total_length_seconds += minutes * 60 + seconds

    # Convert total length to a readable format (HH:MM:SS)
    total_length = str(timedelta(seconds=total_length_seconds))

    # Display the total length in a box
    if total_length_seconds < 2 * 60 * 60:
        st.success(f"We're singing for **{total_length}** 🕺 Keep picking!")
    else:
        st.error(f"Oh no! We're singing for **{total_length}** 😔")

    for i, selected_song in enumerate(st.session_state.selected_songs):
        col1, col2 = st.columns([4, 1])  # Create two columns for the song and button
        with col1:
            st.write(selected_song)  # Display the song
        with col2:
            # Add a remove button for each song with a unique key
            if st.button("❌", key=f"remove_{i}"):
                # Remove the song from the list
                st.session_state.selected_songs.pop(i)
                save_to_google_sheets()
                st.session_state.deleted = True
                st.rerun()  # Rerun the script to update the UI

else:
    st.write("No songs selected. Select up to two hours of songs.")


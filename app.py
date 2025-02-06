import streamlit as st
import requests
from datetime import timedelta
import gspread
from google.oauth2.service_account import Credentials
import json
from streamlit_lottie import st_lottie

if 'access' not in st.session_state:
    st.session_state.access = False

if st.session_state.access is False:
    left, middle, right = st.columns(3)
    with middle:
        try:
            st_lottie("https://lottie.host/70746a4d-f66d-4ffb-afe7-f57abd47766a/5jiEw2onV7.json",height=200)
        except Exception as e:
            st.text("")
        password = st.text_input("", placeholder="Enter password", type='password')
        if (st.button("Login", type="primary") or password):
            if st.secrets["ACCESS_CREDENTIALS"]["password"] == password:
                st.session_state.access = True
                st.rerun()
            else:
                st.toast("Incorrect password", icon="⚠️")

else:
    st.set_page_config(page_title="Tune Timer")
    # Initialize headers and URL for Algolia authentication
    if 'headers' not in st.session_state:
        st.session_state.headers = {
        "x-algolia-application-id": st.secrets["ALGOLIA_CREDENTIALS"]["application_id"],
        "x-algolia-api-key": st.secrets["ALGOLIA_CREDENTIALS"]["api_key"],
        "Content-Type": "application/json"
        }
        st.session_state.url = st.secrets["ALGOLIA_CREDENTIALS"]["endpoint"]

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
            st.toast("Loading songs...", icon="⌛")

        return st.session_state.client

    # Function to fetch the sheet
    def fetch_sheet():
        client = create_client()  # Ensure client is created
        sheet = client.open_by_key(st.session_state.sheet_id).sheet1
        return sheet

    # Initialize session state for selected songs if not already initialized
    if 'selected_songs' not in st.session_state:
        #st.session_state.selected_songs = []
        sheet = fetch_sheet()
        song_list = sheet.get_all_records()
        st.session_state.selected_songs = [item["selected_song"] for item in song_list]

    # Initialize session state for search results if not already initialized
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []

    # Initialize session state for deleted songs
    if 'deleted' not in st.session_state:
        st.session_state.deleted = False
    elif st.session_state.deleted is True:
        st.toast("Song removed", icon="😔")
        st.session_state.deleted = False

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


    ### HEADER ###
    # Streamlit UI
    st.title("⏳ Tune Timer")
    st.write("Search the SYNG song catalog and select your favorite hits. We'll keep track of the time for you.")

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
            if st.button(f"➕{'&nbsp;'*3}{song}", key=f"select_{i}", help="Select song"):
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
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Selected Songs")

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

        remaining_time_seconds = 2 * 60 * 60 - total_length_seconds
        remaining_time = str(timedelta(seconds=remaining_time_seconds))
        
        st.write("Click to remove song")

        # Display the total length in a box

        if total_length_seconds < 2 * 60 * 60:
            with col2:
                st.success(f"We're singing for **{total_length}** 🕺 Keep picking! {remaining_time} remains...")
        else:
            with col2:
                st.error(f"Oh no! We're singing for **{total_length}** 😔")

        for i, selected_song in enumerate(st.session_state.selected_songs):
            if st.button(f"{selected_song}{'&nbsp;'*3}❌", key=f"remove_{i}", help="Remove song"):
                # Remove song fome session state
                st.session_state.selected_songs.pop(i)
                save_to_google_sheets()
                st.session_state.deleted = True
                st.rerun()

    else:
        st.write("No songs selected. Select up to two hours of songs.")


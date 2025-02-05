import streamlit as st
import requests
from datetime import timedelta

# Algolia endpoint
url = "https://vfeb8tk7gw-dsn.algolia.net/1/indexes/*/queries"

# Headers for authentication
headers = {
    "x-algolia-application-id": "VFEB8TK7GW",
    "x-algolia-api-key": "7eb409217eabcd7e10083bcbeee0974a",
    "Content-Type": "application/json"
}

# Initialize session state for selected songs if not already initialized
if 'selected_songs' not in st.session_state:
    st.session_state.selected_songs = []

# Initialize session state for search results if not already initialized
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

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
        response = requests.post(url, json=payload, headers=headers)

        # Checking the response
        if response.status_code == 200:
            data = response.json()
            if 'results' in data and len(data['results'][0]['hits']) > 0:
                # Store search results in session state
                st.session_state.search_results = data['results'][0]['hits']
            else:
                st.session_state.search_results = []
                st.write("No results found.")
        else:
            st.write(f"Request failed: {response.status_code}, {response.text}")

# Display search results and handle song selection
if st.session_state.search_results:
    st.subheader("Search results")
    for i, hit in enumerate(st.session_state.search_results):
        song = f"{hit['artistITSO']} - {hit['title']} ({hit['length']})"
        
        # Display a button for each song with a unique key
        if st.button(f"{song}", key=f"select_{i}"):
            # Add selected song to session state
            if song not in st.session_state.selected_songs:
                st.session_state.selected_songs.append(song)

# Display selected songs with a remove button for each
st.divider()
st.subheader("Selected Songs")

if st.session_state.selected_songs:
    # Calculate total length of selected songs
    total_length_seconds = 0
    for song in st.session_state.selected_songs:
        # Extract the length from the song string (assuming format "Length: MM:SS")
        time_start = song.find("(") + 1  # Find the index of "(" and move 1 character ahead
        time_end = song.find(")")        # Find the index of ")"
        length_str = song[time_start:time_end] # Slice the string to get the time
        minutes, seconds = map(int, length_str.split(":"))
        total_length_seconds += minutes * 60 + seconds

    # Convert total length to a readable format (HH:MM:SS)
    total_length = str(timedelta(seconds=total_length_seconds))

    # Display the total length in a box
    st.info(f"Total time: **{total_length}**")

    for i, selected_song in enumerate(st.session_state.selected_songs):
        col1, col2 = st.columns([4, 1])  # Create two columns for the song and button
        with col1:
            st.write(selected_song)  # Display the song
        with col2:
            # Add a remove button for each song with a unique key
            if st.button("❌", key=f"remove_{i}"):
                # Remove the song from the list
                st.session_state.selected_songs.pop(i)
                st.rerun()  # Rerun the script to update the UI

else:
    st.write("No songs selected.")


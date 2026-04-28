import streamlit as st
import requests
import os

# ======== Page Config (streamlit) =========
st.set_page_config(page_title="Travel Recommendation System", page_icon="🧳")

st.title("🧳 Travel Recommendation Engine")
st.write("Welcome. Let's verify the microservices are talking to each other to officially complete Phase 1.")

# Default to http://backend:8000 (FastAPI container).
BACKEND_URL = os.getenv("API_URL", "http://backend:8000")

st.subheader("System Diagnostics")

# Simple button to trigger API call
if st.button("Ping Backend & Databases"):
    with st.spinner("Pinging FastAPI server..."):
        try:
            # Send GET request to the root endpoint
            response = requests.get(f"{BACKEND_URL}/")
            
            if response.status_code == 200:
                st.success("Successful connection to FastAPI Backend.")
                
                # Display the JSON payload Irina's endpoint returns
                data = response.json()
                st.json(data)
                
                if "databases" in data:
                    st.info("Backend also successfully connected to databases.")
            else:
                st.warning(f"ERR: Backend responded with an error code: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            st.error("ERR: Failed to GET request backend. Check backend execution.")
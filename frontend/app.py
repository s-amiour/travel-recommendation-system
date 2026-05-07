import streamlit as st
import requests
import os

st.set_page_config(page_title="Travel Recommendation System", page_icon="🧳")

BACKEND_URL = os.getenv("API_URL", "http://backend:8000")

st.title("🧳 Travel Recommendation Engine")

USER_IDS = [f"bot_user_{i}" for i in range(1, 21)]

PRESET_CITIES = {
    "Paris": (48.8566, 2.3522),
    "London": (51.5074, -0.1278),
    "New York": (40.7128, -74.0060),
    "Tokyo": (35.6762, 139.6503),
    "Dubai": (25.2048, 55.2708),
}

user_id = st.selectbox("Select bot user", USER_IDS)

city = st.selectbox("Preset city", list(PRESET_CITIES.keys()))
default_lat, default_lng = PRESET_CITIES[city]

lat = st.number_input("Latitude", value=default_lat, format="%.6f")
lng = st.number_input("Longitude", value=default_lng, format="%.6f")


def visit_destination(destination_id):
    try:
        response = requests.post(
            f"{BACKEND_URL}/destinations/{destination_id}/visit",
            timeout=10,
        )
        response.raise_for_status()
        st.success("Visit recorded!")
    except requests.RequestException as e:
        st.error(f"Visit failed: {e}")


def render_destination_card(destination, show_trending_score=False):
    destination_id = destination.get("id") or destination.get("destination_id")

    with st.container(border=True):
        st.subheader(destination.get("name", "Unknown destination"))

        if destination.get("country"):
            st.write(f"**Country:** {destination['country']}")

        if destination.get("city"):
            st.write(f"**City:** {destination['city']}")

        if destination.get("description"):
            st.write(destination["description"])

        if show_trending_score:
            st.write(f"**Trending score:** {destination.get('trending_score', 0)}")

        if destination_id:
            if st.button("Visit / Read More", key=f"visit-{destination_id}"):
                visit_destination(destination_id)


if st.button("Get recommendations"):
    try:
        response = requests.get(
            f"{BACKEND_URL}/dashboard/{user_id}",
            params={"lat": lat, "lng": lng},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        st.header("Network Recommendations")
        for destination in data.get("recommendations", []):
            render_destination_card(destination)

        st.header("Trending Globally")
        for destination in data.get("trending", []):
            render_destination_card(destination, show_trending_score=True)

        st.header("Nearby Discoveries")
        for destination in data.get("nearby", []):
            render_destination_card(destination)

    except requests.RequestException as e:
        st.error(f"Backend request failed: {e}")
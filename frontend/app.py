import streamlit as st
import requests
import os
import pandas as pd

# ======== 1. Page Config & State Setup =========
st.set_page_config(page_title="Travel Recommendation System", page_icon="🧳", layout="wide")

BACKEND_URL = os.getenv("API_URL", "http://backend:8000")

if "dashboard_data" not in st.session_state:
    st.session_state.dashboard_data = None

# ======== 2. The Pop-up Dialog =========
@st.dialog("Destination Overview")
def show_destination_popup(dest):
    st.markdown(f"## {dest.get('name', 'Unknown Destination')}")
    
    # Inline metadata tags
    tags = [
        f"**Category:** {dest.get('category', 'N/A').title()}",
        f"**Price Tier:** {dest.get('price_tier', 'N/A')}",
        f"**Climate:** {dest.get('climate', 'N/A').title()}",
        f"**Status:** {dest.get('status', 'N/A').title()}"
    ]
    st.markdown(" | ".join(tags))
    st.divider()
    
    # Deep Information
    st.write(dest.get("description", "No detailed description available at this time."))
    
    if dest.get("fun_facts"):
        st.markdown("### 💡 Fun Facts")
        for fact in dest["fun_facts"]:
            st.markdown(f"- {fact}")
            
    # Optional: Render a mini-map if coordinates exist
    coords = dest.get("location", {}).get("coordinates")
    if coords and len(coords) == 2:
        st.markdown("### 🗺️ Location")
        # Streamlit map requires a dataframe with 'lat' and 'lon' (Note: MongoDB is [lng, lat])
        df = pd.DataFrame([{"lat": coords[1], "lon": coords[0]}])
        st.map(df, zoom=4)


# ======== 3. Helper Functions =========
def trigger_visit_and_show(dest, user_id, current_lat, current_lng):
    """Hits Redis, refreshes background state, and opens the popup."""
    dest_id = dest.get("_id") or dest.get("id") or dest.get("destination_id")
    try:
        # 1. Log the visit (updates Redis)
        requests.post(f"{BACKEND_URL}/destinations/{dest_id}/visit", timeout=5)
        st.toast("✅ Visit recorded! Score updated in the background.")
        
        # 2. Silently re-fetch the dashboard data so it's fresh when the dialog closes
        updated_response = requests.get(
            f"{BACKEND_URL}/dashboard/{user_id}",
            params={"lat": current_lat, "lng": current_lng},
            timeout=10
        )
        st.session_state.dashboard_data = updated_response.json()
        
    except Exception as e:
        st.error(f"Failed to record visit: {e}")
        
    # 3. Open the modal
    show_destination_popup(dest)


def render_destination_card(dest, context="", user_id="", current_lat=0.0, current_lng=0.0):
    """Renders a unified card format based on the data tier"""
    with st.container(border=True):
        st.subheader(dest.get("name", "Unknown Destination"))
        
        # Meta tags
        meta = []
        if dest.get("category"): meta.append(f"🏷️ {dest['category'].title()}")
        if dest.get("price_tier"): meta.append(f"💵 {dest['price_tier']}")
        if dest.get("distance_in_meters"): meta.append(f"📍 {int(dest['distance_in_meters'])/1000:.1f} km away")
        
        if meta:
            st.caption(" | ".join(meta))
            
        # Contextual Scores
        if context == "social" and dest.get("social_score"):
            st.success(f"👥 Recommended by {dest['social_score']} friends!")
        elif context == "trending" and dest.get("trending_score"):
            st.info(f"🔥 Trending Score: {dest['trending_score']}")
            
        # The Action Button
        if st.button("Visit / Read More", key=f"btn_{context}_{dest.get('_id', dest.get('destination_id'))}", use_container_width=True):
            trigger_visit_and_show(dest, user_id, current_lat, current_lng)


# ======== 4. Sidebar: Context UI =========
with st.sidebar:
    st.title("⚙️ User Context")
    st.write("Simulate the environment:")
    
    USER_IDS = [f"bot_user_{i}" for i in range(1, 21)]
    user_id = st.selectbox("Select Bot User", USER_IDS)

    st.divider()
    
    PRESET_CITIES = {
        "Paris, FR": (48.8566, 2.3522),
        "London, UK": (51.5074, -0.1278),
        "New York, USA": (40.7128, -74.0060),
        "Tokyo, JP": (35.6762, 139.6503),
        "Dubai, UAE": (25.2048, 55.2708),
        "Grand Canyon, USA": (36.1069, -112.1129)
    }
    
    city = st.selectbox("Teleport to City", list(PRESET_CITIES.keys()))
    default_lat, default_lng = PRESET_CITIES[city]

    lat = st.number_input("Latitude", value=default_lat, format="%.6f")
    lng = st.number_input("Longitude", value=default_lng, format="%.6f")
    
    st.divider()
    
    if st.button("🚀 Load Dashboard", use_container_width=True, type="primary"):
        with st.spinner("Crunching graph, geospatial, and cache data..."):
            try:
                response = requests.get(
                    f"{BACKEND_URL}/dashboard/{user_id}",
                    params={"lat": lat, "lng": lng},
                    timeout=10,
                )
                response.raise_for_status()
                st.session_state.dashboard_data = response.json()
            except requests.RequestException as e:
                st.error(f"Backend offline or error: {e}")

# ======== 5. Main UI Layout =========
st.title("🧳 Polyglot Travel Engine")

if not st.session_state.dashboard_data:
    st.info("👈 Select your context in the sidebar and click **Load Dashboard** to begin.")
else:
    data = st.session_state.dashboard_data
    
    tab1, tab2, tab3 = st.tabs(["👥 Network Picks (Neo4j)", "🔥 Trending Globally (Redis)", "📍 Nearby (MongoDB)"])
    
    with tab1:
        st.header("Recommended by your network")
        recs = data.get("recommendations", [])
        if not recs:
            st.warning("Your network hasn't rated anything highly yet! Be the first.")
        else:
            cols = st.columns(3)
            for i, dest in enumerate(recs):
                with cols[i % 3]:
                    render_destination_card(dest, "social", user_id, lat, lng)
                    
    with tab2:
        st.header("Top 5 Destinations Right Now")
        trends = data.get("trending", [])
        if not trends:
            st.warning("No trending data available.")
        else:
            cols = st.columns(3)
            for i, dest in enumerate(trends):
                with cols[i % 3]:
                    render_destination_card(dest, "trending", user_id, lat, lng)
                    
    with tab3:
        st.header("Discoveries near you")
        nearby = data.get("nearby", [])
        if not nearby:
            st.warning("Nothing found within 50km.")
        else:
            cols = st.columns(3)
            for i, dest in enumerate(nearby):
                with cols[i % 3]:
                    render_destination_card(dest, "nearby", user_id, lat, lng)
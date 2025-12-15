import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Realtime Flood Alert", layout="wide")

USGS_URL = "https://waterservices.usgs.gov/nwis/iv/?format=json&sites=01646500&parameterCd=00065"

@st.cache_data(ttl=60)
def fetch_river_data():
    r = requests.get(USGS_URL)
    data = r.json()
    ts = data["value"]["timeSeries"][0]["values"][0]["value"]
    df = pd.DataFrame(ts)
    df["value"] = df["value"].astype(float)
    df["dateTime"] = pd.to_datetime(df["dateTime"])
    return df.tail(50)

st.title("🌊 Realtime Flood Monitoring Dashboard")

placeholder = st.empty()

while True:
    with placeholder.container():
        df = fetch_river_data()
        current_level = df["value"].iloc[-1]

        col1, col2, col3 = st.columns(3)

        col1.metric("Current River Level (ft)", round(current_level, 2))
        col2.metric("Status", "⚠️ Flood Risk" if current_level > 7 else "✅ Normal")
        col3.metric("Last Updated", datetime.now().strftime("%H:%M:%S"))

        fig = px.line(
            df,
            x="dateTime",
            y="value",
            title="Realtime River Level Trend",
            markers=True
        )

        st.plotly_chart(fig, use_container_width=True)

        if current_level > 7:
            st.error("🚨 FLOOD ALERT: River level is high!")
        else:
            st.success("✅ River conditions are normal")

    time.sleep(30)

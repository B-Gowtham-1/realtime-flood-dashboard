import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Realtime Flood Alert Dashboard",
    layout="wide"
)

USGS_URL = "https://waterservices.usgs.gov/nwis/iv/?format=json&sites=01646500&parameterCd=00065"

# ---------------- DATA FETCH ----------------
@st.cache_data(ttl=60)
def fetch_river_data():
    start_time = time.time()

    r = requests.get(USGS_URL)
    data = r.json()
    ts = data["value"]["timeSeries"][0]["values"][0]["value"]

    df = pd.DataFrame(ts)
    df["value"] = df["value"].astype(float)
    df["dateTime"] = pd.to_datetime(df["dateTime"])

    latency = time.time() - start_time
    return df.tail(50), latency

# ---------------- UI ----------------
st.title("🌊 Realtime Flood Monitoring & Prediction System")
st.caption("Low-latency fog-cloud based realtime disaster alert streaming")

# User-defined threshold
threshold = st.slider(
    "Flood Alert Threshold (River Level in feet)",
    min_value=5.0,
    max_value=15.0,
    value=7.0,
    step=0.5
)

placeholder = st.empty()

while True:
    with placeholder.container():
        # Measure total latency
        total_start = time.time()

        df, api_latency = fetch_river_data()
        current_level = df["value"].iloc[-1]

        # Simple prediction (next-step trend)
        predicted_level = df["value"].tail(5).mean()

        total_latency = time.time() - total_start

        # ----------- METRICS ROW -----------
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Current River Level (ft)", round(current_level, 2))
        col2.metric("Predicted Level (ft)", round(predicted_level, 2))
        col3.metric("API Latency (sec)", round(api_latency, 3))
        col4.metric("Total System Latency (sec)", round(total_latency, 3))

        # ----------- STATUS -----------
        if predicted_level > threshold:
            st.error("🚨 FLOOD RISK PREDICTED – PROACTIVE ALERT")
            status = "High Risk"
        else:
            st.success("✅ NORMAL – No Immediate Flood Risk")
            status = "Normal"

        # ----------- GRAPH -----------
        fig = px.line(
            df,
            x="dateTime",
            y="value",
            markers=True,
            title="Realtime River Level Trend"
        )

        fig.add_hline(
            y=threshold,
            line_dash="dash",
            line_color="red",
            annotation_text="Alert Threshold"
        )

        st.plotly_chart(fig, use_container_width=True)

        # ----------- FOOTER INFO -----------
        st.write("**Prediction Status:**", status)
        st.write("**Last Updated:**", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    time.sleep(30)

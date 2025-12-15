import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Realtime Flood Intelligence Dashboard", layout="wide")

# ---------------- APIs ----------------
USGS_URL = "https://waterservices.usgs.gov/nwis/iv/?format=json&sites=01646500&parameterCd=00065"
NOAA_ALERTS = "https://api.weather.gov/alerts/active"
METEO_URL = "https://api.open-meteo.com/v1/forecast?latitude=38.9&longitude=-77.0&hourly=precipitation,temperature_2m"

# ---------------- DATA FUNCTIONS ----------------
@st.cache_data(ttl=60)
def fetch_river():
    t0 = time.time()
    r = requests.get(USGS_URL)
    data = r.json()
    ts = data["value"]["timeSeries"][0]["values"][0]["value"]
    df = pd.DataFrame(ts)
    df["value"] = df["value"].astype(float)
    df["dateTime"] = pd.to_datetime(df["dateTime"])
    latency = time.time() - t0
    return df.tail(50), latency

@st.cache_data(ttl=300)
def fetch_weather():
    r = requests.get(METEO_URL)
    data = r.json()
    rain = data["hourly"]["precipitation"][0]
    temp = data["hourly"]["temperature_2m"][0]
    return rain, temp

@st.cache_data(ttl=300)
def fetch_alerts():
    r = requests.get(NOAA_ALERTS)
    data = r.json()
    if len(data["features"]) > 0:
        alert = data["features"][0]["properties"]
        return alert["event"], alert["severity"]
    return "No Active Alerts", "None"

# ---------------- UI ----------------
st.title("🌊 Realtime Flood Intelligence & Alert System")
st.caption("Low-latency fog–cloud framework with realtime prediction & monitoring")

threshold = st.slider("Flood Threshold (ft)", 5.0, 15.0, 7.0, 0.5)

container = st.empty()

while True:
    with container.container():
        start_total = time.time()

        df, api_latency = fetch_river()
        rain, temp = fetch_weather()
        alert, severity = fetch_alerts()

        current = df["value"].iloc[-1]
        predicted = df["value"].tail(5).mean()
        total_latency = time.time() - start_total

        # -------- METRICS --------
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("River Level (ft)", round(current, 2))
        c2.metric("Predicted Level (ft)", round(predicted, 2))
        c3.metric("Rainfall (mm)", rain)
        c4.metric("Temperature (°C)", temp)

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Prediction Status", "High Risk" if predicted > threshold else "Normal")
        c6.metric("API Latency (s)", round(api_latency, 3))
        c7.metric("System Latency (s)", round(total_latency, 3))
        c8.metric("NOAA Alert", alert)

        # -------- STATUS --------
        if predicted > threshold:
            st.error(f"🚨 FLOOD RISK PREDICTED | Severity: {severity}")
        else:
            st.success("✅ No Immediate Flood Risk")

        # -------- GRAPH --------
        fig = px.line(
            df,
            x="dateTime",
            y="value",
            markers=True,
            title="Realtime River Level Trend"
        )
        fig.add_hline(y=threshold, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

        st.write("**Last Updated:**", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.write("**Data Sources:** USGS | NOAA | Open-Meteo")

    time.sleep(30)

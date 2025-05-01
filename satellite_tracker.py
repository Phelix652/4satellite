import streamlit as st
import requests
from skyfield.api import load, EarthSatellite
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

# Streamlit configuration
st.set_page_config(layout="wide")
st.title("🌍 Live Satellite Tracker")
st.markdown("Track the ISS, NOAA satellites, and more in real-time")

# User location inputs
col1, col2 = st.columns(2)
with col1:
    my_lat = st.number_input("Your Latitude", value=16.8409)
with col2:
    my_lon = st.number_input("Your Longitude", value=96.1735)

# --- Fetch TLE Data Functions with Caching ---
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_tle_iss():
    try:
        url = "https://celestrak.org/NORAD/elements/stations.txt"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        lines = response.text.strip().split("\n")
        for i in range(0, len(lines), 3):
            if "ISS (ZARYA)" in lines[i]:
                return lines[i], lines[i+1], lines[i+2]
        raise ValueError("ISS not found in data")
    except Exception as e:
        st.error(f"Error fetching ISS data: {str(e)}")
        return None, None, None

@st.cache_data(ttl=3600)
def get_tle_noaa():
    try:
        url = "https://celestrak.org/NORAD/elements/weather.txt"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        lines = response.text.strip().split("\n")
        for i in range(0, len(lines), 3):
            if "NOAA 15" in lines[i]:
                return lines[i], lines[i+1], lines[i+2]
        raise ValueError("NOAA 15 not found in data")
    except Exception as e:
        st.error(f"Error fetching NOAA data: {str(e)}")
        return None, None, None

@st.cache_data(ttl=3600)
def get_tle_tianmu():
    try:
        url = "https://celestrak.org/NORAD/elements/weather.txt"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        lines = response.text.strip().split("\n")
        for i in range(0, len(lines), 3):
            if "TIANMU-1 14" in lines[i]:
                return lines[i], lines[i+1], lines[i+2]
        raise ValueError("TIANMU-1 14 not found in data")
    except Exception as e:
        st.error(f"Error fetching TIANMU data: {str(e)}")
        return None, None, None

@st.cache_data(ttl=3600)
def get_tle_meteor():
    try:
        url = "https://celestrak.org/NORAD/elements/weather.txt"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        lines = response.text.strip().split("\n")
        for i in range(0, len(lines), 3):
            if "METEOR-M 2 4" in lines[i] or "METEOR-M2 4" in lines[i]:
                return lines[i], lines[i+1], lines[i+2]
        raise ValueError("METEOR-M2 4 not found in data")
    except Exception as e:
        st.error(f"Error fetching METEOR data: {str(e)}")
        return None, None, None

# --- Get Satellite Position and Path ---
def get_satellite_data(satellite, ts):
    time_now = ts.now()
    geocentric = satellite.at(time_now)
    subpoint = geocentric.subpoint()
    lat = subpoint.latitude.degrees
    lon = subpoint.longitude.degrees

    times = ts.utc(time_now.utc_datetime().year,
                   time_now.utc_datetime().month,
                   time_now.utc_datetime().day,
                   np.linspace(0, 24, 100))
    positions = [satellite.at(t).subpoint() for t in times]
    lats = [pos.latitude.degrees for pos in positions]
    lons = [pos.longitude.degrees for pos in positions]

    return lat, lon, lats, lons

# --- Main App Function ---
def main():
    ts = load.timescale()
    
    # Load all satellites
    satellites = []
    sat_objects = []
    
    # ISS
    name_iss, tle1_iss, tle2_iss = get_tle_iss()
    if None not in (name_iss, tle1_iss, tle2_iss):
        sat_iss = EarthSatellite(tle1_iss, tle2_iss, name_iss, ts)
        sat_objects.append((sat_iss, 'yellow', 'ISS'))
    
    # NOAA 15
    name_noaa, tle1_noaa, tle2_noaa = get_tle_noaa()
    if None not in (name_noaa, tle1_noaa, tle2_noaa):
        sat_noaa = EarthSatellite(tle1_noaa, tle2_noaa, name_noaa, ts)
        sat_objects.append((sat_noaa, 'red', 'NOAA 15'))
    
    # TIANMU-1 14
    name_tianmu, tle1_tianmu, tle2_tianmu = get_tle_tianmu()
    if None not in (name_tianmu, tle1_tianmu, tle2_tianmu):
        sat_tianmu = EarthSatellite(tle1_tianmu, tle2_tianmu, name_tianmu, ts)
        sat_objects.append((sat_tianmu, 'magenta', 'TIANMU-1 14'))
    
    # METEOR-M2 4
    name_meteor, tle1_meteor, tle2_meteor = get_tle_meteor()
    if None not in (name_meteor, tle1_meteor, tle2_meteor):
        sat_meteor = EarthSatellite(tle1_meteor, tle2_meteor, name_meteor, ts)
        sat_objects.append((sat_meteor, 'lime', 'METEOR-M2 4'))

    if not sat_objects:
        st.error("No satellite data available. Please try again later.")
        return

    # Create the map
    fig, ax = plt.subplots(figsize=(12, 6))
    m = Basemap(projection='cyl', resolution='c')
    m.drawcoastlines()
    m.drawcountries()
    m.drawmapboundary(fill_color='midnightblue')
    m.fillcontinents(color='forestgreen', lake_color='darkgreen')
    m.drawparallels(np.arange(-90., 91., 30.))
    m.drawmeridians(np.arange(-180., 181., 60.))

    # Plot user location
    x_my, y_my = m(my_lon, my_lat)
    ax.scatter(x_my, y_my, color='white', marker='^', s=100, label="Your Location")

    # Plot each satellite
    for sat, color, name in sat_objects:
        lat, lon, path_lats, path_lons = get_satellite_data(sat, ts)
        x, y = m(lon, lat)
        ax.scatter(x, y, color=color, s=100, label=name)
        path_x, path_y = m(path_lons, path_lats)
        ax.plot(path_x, path_y, linestyle='--', color=color, alpha=0.5)

    # Add legend and display
    ax.legend(loc='lower left')
    st.pyplot(fig)

    # Add info about when data was loaded
    st.caption(f"Data last updated: {ts.now().utc_datetime().strftime('%Y-%m-%d %H:%M:%S UTC')}")

if __name__ == "__main__":
    main()
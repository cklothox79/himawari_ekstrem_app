# ============================================================
# HIMAWARI-8 MULTI BAND EXTREME WEATHER ANALYSIS
# PUTING BELIUNG – STABLE VERSION (ANTI CRASH)
# ============================================================

import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# ============================================================
DATA_DIR = Path("data_nc")
BANDS = ["B07", "B08", "B09", "B10", "B13", "B15"]
KM_PER_PIXEL = 2.0

st.set_page_config(page_title="Analisis Puting Beliung – Himawari", layout="wide")

# ============================================================
def find_nearest_index(array, value):
    return int(np.abs(array - value).argmin())

def mean_radius_tbb_safe(tbb, lat, lon, lat0, lon0, radius_km):
    iy = find_nearest_index(lat, lat0)
    ix = find_nearest_index(lon, lon0)

    r_pix = int(radius_km / KM_PER_PIXEL)

    y0 = max(0, iy - r_pix)
    y1 = min(len(lat), iy + r_pix)
    x0 = max(0, ix - r_pix)
    x1 = min(len(lon), ix + r_pix)

    window = tbb.values[y0:y1, x0:x1]
    return float(np.nanmean(window))

def load_band(band):
    files = sorted((DATA_DIR / band).glob("*.nc"))
    data = []
    times = []

    for f in files:
        ds = xr.open_dataset(f)
        tbb = ds["tbb"]
        lat = ds["latitude"].values
        lon = ds["longitude"].values

        time_str = f.stem.split("_")[-1]
        time = datetime.strptime(time_str, "%Y%m%d%H%M")

        data.append((tbb, lat, lon))
        times.append(time)

    return data, times

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("📍 Lokasi Analisis")
lat0 = st.sidebar.number_input("Lintang (°)", value=-7.3735, format="%.4f")
lon0 = st.sidebar.number_input("Bujur (°)", value=112.7938, format="%.4f")
radius_km = st.sidebar.slider("Radius (km)", 2, 20, 5)

# ============================================================
# LOAD DATA
# ============================================================
band_data = {}
band_times = {}

for band in BANDS:
    data, times = load_band(band)
    band_data[band] = data
    band_times[band] = times

times = band_times["B13"]

# ============================================================
# TIME SERIES
# ============================================================
records = []

for i, t in enumerate(times):
    row = {"Time": t}
    try:
        for band in BANDS:
            tbb, lat, lon = band_data[band][i]
            row[band] = mean_radius_tbb_safe(
                tbb, lat, lon, lat0, lon0, radius_km
            )
        records.append(row)
    except:
        continue

df = pd.DataFrame(records).set_index("Time")

# ============================================================
# INDEKS
# ============================================================
df["Updraft_Index"] = df["B07"] - df["B13"]
df["Rapid_Cooling"] = df["B13"].diff()
df["Dry_Intrusion"] = df["B10"].diff()
df["Turbulence"] = abs(df["B13"] - df["B15"])

# ============================================================
# KLASIFIKASI
# ============================================================
def classify(r):
    if r["Updraft_Index"] <= -5 and (r["Rapid_Cooling"] <= -3 or r["Dry_Intrusion"] >= 1.5):
        return "🌪️ POTENSI PUTING BELIUNG"
    elif r["Updraft_Index"] <= -5:
        return "⛈️ KONVEKSI KUAT LOKAL"
    else:
        return "🌤️ KONVEKSI BIASA"

df["Kesimpulan"] = df.apply(classify, axis=1)

# ============================================================
# OUTPUT
# ============================================================
st.title("🌪️ Analisis Puting Beliung – Himawari-8")
st.dataframe(df.round(2), use_container_width=True)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df.index, df["Updraft_Index"], label="Updraft Index")
ax.plot(df.index, df["Rapid_Cooling"], label="Rapid Cooling")
ax.plot(df.index, df["Dry_Intrusion"], label="Dry Intrusion")
ax.legend()
ax.grid(True)
st.pyplot(fig)

st.success(df["Kesimpulan"].value_counts().idxmax())

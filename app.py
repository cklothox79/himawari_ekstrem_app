# ============================================================
# HIMAWARI-8 PUTING BELIUNG – DEBUG STABLE VERSION
# ============================================================

import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Himawari Puting Beliung", layout="wide")

DATA_DIR = Path("data_nc")
BANDS = ["B07", "B08", "B09", "B10", "B13", "B15"]
KM_PER_PIXEL = 2.0

# ============================================================
def find_nearest_index(arr, val):
    return int(np.abs(arr - val).argmin())

def mean_radius_safe(tbb, lat, lon, lat0, lon0, radius_km):
    iy = find_nearest_index(lat, lat0)
    ix = find_nearest_index(lon, lon0)
    r = int(radius_km / KM_PER_PIXEL)

    y0, y1 = max(0, iy-r), min(len(lat), iy+r)
    x0, x1 = max(0, ix-r), min(len(lon), ix+r)

    return float(np.nanmean(tbb.values[y0:y1, x0:x1]))

def load_band(band):
    folder = DATA_DIR / band
    files = sorted(folder.glob("*.nc"))
    data = []

    for f in files:
        try:
            ds = xr.open_dataset(f)
            data.append({
                "time": datetime.strptime(f.stem.split("_")[-1], "%Y%m%d%H%M"),
                "tbb": ds["tbb"],
                "lat": ds["latitude"].values,
                "lon": ds["longitude"].values
            })
        except Exception as e:
            st.warning(f"Gagal baca {f.name}: {e}")

    return data

# ============================================================
st.sidebar.header("📍 Lokasi")
lat0 = st.sidebar.number_input("Lintang", value=-7.3735)
lon0 = st.sidebar.number_input("Bujur", value=112.7938)
radius_km = st.sidebar.slider("Radius (km)", 2, 20, 5)

# ============================================================
# LOAD SEMUA BAND
# ============================================================
band_data = {}
lengths = {}

st.subheader("🧪 Cek Jumlah File per Band")

for band in BANDS:
    data = load_band(band)
    band_data[band] = data
    lengths[band] = len(data)
    st.write(f"{band}: {len(data)} file")

min_len = min(lengths.values())

if min_len == 0:
    st.error("❌ Ada band tanpa data. Periksa folder data_nc.")
    st.stop()

st.info(f"Sinkronisasi ke {min_len} timestep")

# ============================================================
# HITUNG TIME SERIES
# ============================================================
records = []

for i in range(min_len):
    row = {"Time": band_data["B13"][i]["time"]}
    try:
        for band in BANDS:
            d = band_data[band][i]
            row[band] = mean_radius_safe(
                d["tbb"], d["lat"], d["lon"], lat0, lon0, radius_km
            )
        records.append(row)
    except Exception as e:
        st.warning(f"Gagal timestep {i}: {e}")

df = pd.DataFrame(records)

if df.empty:
    st.error("❌ DataFrame kosong. Tidak ada data valid.")
    st.stop()

df.set_index("Time", inplace=True)

# ============================================================
# INDEKS
# ============================================================
df["Updraft"] = df["B07"] - df["B13"]
df["RapidCooling"] = df["B13"].diff()
df["DryIntrusion"] = df["B10"].diff()
df["Turbulence"] = abs(df["B13"] - df["B15"])

# ============================================================
# KESIMPULAN
# ============================================================
def classify(r):
    if r["Updraft"] <= -5 and (r["RapidCooling"] <= -3 or r["DryIntrusion"] >= 1.5):
        return "🌪️ POTENSI PUTING BELIUNG"
    elif r["Updraft"] <= -5:
        return "⛈️ KONVEKSI KUAT"
    else:
        return "🌤️ KONVEKSI BIASA"

df["Status"] = df.apply(classify, axis=1)

# ============================================================
# OUTPUT
# ============================================================
st.subheader("📊 Tabel Analisis")
st.dataframe(df.round(2), use_container_width=True)

st.subheader("📈 Grafik Indeks")
try:
    fig, ax = plt.subplots()
    ax.plot(df.index, df["Updraft"], label="Updraft")
    ax.plot(df.index, df["RapidCooling"], label="Rapid Cooling")
    ax.plot(df.index, df["DryIntrusion"], label="Dry Intrusion")
    ax.legend()
    st.pyplot(fig)
except Exception as e:
    st.warning(f"Gagal plot grafik: {e}")

st.success(df["Status"].value_counts().idxmax())

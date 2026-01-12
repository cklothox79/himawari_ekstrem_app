# ==========================================================
#  APP.PY FINAL – MULTI-BAND HIMAWARI (STREAMLIT CLOUD SAFE)
# ==========================================================

import streamlit as st
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================================
#  KONFIGURASI
# ==========================================================
st.set_page_config(page_title="Himawari Puting Beliung", layout="wide")
DATA_DIR = Path("data")
BANDS = ["B07", "B08", "B13", "B15"]

# ==========================================================
#  FUNGSI UTILITAS
# ==========================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def mean_tbb_radius(ds, lat0, lon0, radius_km):
    lat = ds["latitude"].values
    lon = ds["longitude"].values
    tbb = ds["tbb"].values

    lat2d, lon2d = np.meshgrid(lat, lon, indexing="ij")
    dist = haversine(lat0, lon0, lat2d, lon2d)
    mask = dist <= radius_km

    if not np.any(mask):
        return np.nan

    return float(np.nanmean(tbb[mask]))

def read_nc_safe(nc_file):
    try:
        with xr.open_dataset(
            nc_file,
            engine="h5netcdf",
            decode_times=False,
            chunks={}
        ) as ds:
            return ds.load()
    except Exception as e:
        st.warning(f"Gagal baca {nc_file.name}")
        return None

# ==========================================================
#  UI INPUT
# ==========================================================
st.title("🌪️ Analisis Puting Beliung – Himawari-8 (Multi-Band)")

col1, col2, col3 = st.columns(3)
with col1:
    lat0 = st.number_input("Lintang (°)", value=-7.37, format="%.4f")
with col2:
    lon0 = st.number_input("Bujur (°)", value=112.79, format="%.4f")
with col3:
    radius = st.slider("Radius Analisis (km)", 2, 10, 3)

st.markdown("---")

# ==========================================================
#  PROSES DATA
# ==========================================================
results = {}

for band in BANDS:
    band_dir = DATA_DIR / band
    if not band_dir.exists():
        continue

    values = []
    times = []

    nc_files = sorted(band_dir.glob("*.nc"))[:8]  # HARD LIMIT CLOUD

    for nc in nc_files:
        ds = read_nc_safe(nc)
        if ds is None:
            continue

        mean_val = mean_tbb_radius(ds, lat0, lon0, radius)
        if not np.isnan(mean_val):
            values.append(mean_val - 273.15)  # K → °C
            times.append(nc.stem[-4:])

    if values:
        results[band] = pd.DataFrame({
            "time": times,
            "mean_tbb": values
        })

# ==========================================================
#  TAMPILKAN HASIL
# ==========================================================
if not results:
    st.error("❌ Tidak ada data yang berhasil diproses")
    st.stop()

st.subheader("📊 Time Series Mean TBB")

fig, ax = plt.subplots()
for band, df in results.items():
    ax.plot(df["time"], df["mean_tbb"], marker="o", label=band)

ax.set_ylabel("Mean TBB (°C)")
ax.set_xlabel("Waktu (UTC)")
ax.legend()
ax.grid(True)
st.pyplot(fig)

# ==========================================================
#  ANALISIS PUTING BELIUNG
# ==========================================================
st.subheader("🧠 Analisis Otomatis")

msg = []

if "B13" in results:
    tbb13 = results["B13"]["mean_tbb"].values
    if len(tbb13) >= 2:
        cooling = tbb13[-1] - tbb13[0]
        if cooling <= -6:
            msg.append("❄️ Rapid cooling signifikan pada B13")

if "B07" in results and "B13" in results:
    diff = results["B07"]["mean_tbb"].values - results["B13"]["mean_tbb"].values
    if np.nanmean(diff) <= -5:
        msg.append("💨 Indikasi dry intrusion (B07-B13)")

if msg:
    st.error("⚠️ **INDIKASI KUAT PUTING BELIUNG**")
    for m in msg:
        st.write("•", m)
else:
    st.info("🌧️ Dominan konveksi hujan, indikasi vorteks lemah")

st.caption("Analisis berbasis TBB Himawari-8 | Streamlit Cloud Safe")

# =========================================================
# 🛰️ HIMAWARI EXTREME WEATHER ANALYSIS – STAGE 4
# Rapid Cooling Detection (Puting Beliung Indicator)
# =========================================================

import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import re
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document

# =========================================================
# KONFIGURASI
# =========================================================
st.set_page_config(page_title="Analisis Cuaca Ekstrem Himawari", layout="centered")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data_nc"

# =========================================================
# FUNGSI
# =========================================================
def find_nearest_pixel(lat2d, lon2d, lat0, lon0):
    dist2 = (lat2d - lat0)**2 + (lon2d - lon0)**2
    return np.unravel_index(np.argmin(dist2), dist2.shape)


def extract_mean_tbb(ds, lat0, lon0, radius_km):
    tbb = ds["tbb"].values
    lat = ds["latitude"].values
    lon = ds["longitude"].values

    if lat.ndim == 1:
        lon2d, lat2d = np.meshgrid(lon, lat)
    else:
        lat2d, lon2d = lat, lon

    iy, ix = find_nearest_pixel(lat2d, lon2d, lat0, lon0)
    radius_px = int(radius_km / 2)

    y0, y1 = max(iy - radius_px, 0), min(iy + radius_px, tbb.shape[0])
    x0, x1 = max(ix - radius_px, 0), min(ix + radius_px, tbb.shape[1])

    return np.nanmean(tbb[y0:y1, x0:x1]) - 273.15


def parse_band_time(fname):
    band = re.search(r"B(\d{2})", fname).group(1)
    time = re.search(r"_(\d{12})\.nc", fname).group(1)
    return band, time


def classify_rapid_cooling(delta):
    if delta <= -15:
        return "🔴 Rapid Cooling Ekstrem (Puting Beliung)"
    elif delta <= -10:
        return "🟠 Rapid Cooling Kuat"
    elif delta <= -5:
        return "🟡 Pendinginan Cepat"
    else:
        return "🟢 Normal"


# =========================================================
# UI
# =========================================================
st.title("🌪️ Analisis Rapid Cooling – Himawari-8")
st.caption("Deteksi indikasi puting beliung berbasis TBB")

lat0 = st.number_input("Lintang (°)", value=-7.3735, format="%.4f")
lon0 = st.number_input("Bujur (°)", value=112.7938, format="%.4f")
radius_km = st.slider("Radius Analisis (km)", 2, 20, 10)

# =========================================================
# PROSES
# =========================================================
if st.button("▶️ Jalankan Analisis Ekstrem"):
    records = []

    for f in sorted(DATA_DIR.glob("*.nc")):
        try:
            band, time = parse_band_time(f.name)
            ds = xr.open_dataset(f)
            tbb = extract_mean_tbb(ds, lat0, lon0, radius_km)

            records.append({
                "Waktu (UTC)": time,
                "Band": f"B{band}",
                "Mean TBB (°C)": round(tbb, 2)
            })
        except:
            pass

    df = pd.DataFrame(records)
    df["Waktu (UTC)"] = pd.to_datetime(df["Waktu (UTC)"], format="%Y%m%d%H%M")
    df = df.sort_values("Waktu (UTC)")

    # =====================================================
    # RAPID COOLING
    # =====================================================
    df["ΔTBB (°C/10m)"] = df.groupby("Band")["Mean TBB (°C)"].diff()
    df["Status Rapid Cooling"] = df["ΔTBB (°C/10m)"].apply(classify_rapid_cooling)

    st.subheader("📊 Tabel Analisis Rapid Cooling")
    st.dataframe(df, use_container_width=True)

    # =====================================================
    # GRAFIK
    # =====================================================
    fig, ax = plt.subplots()
    for band in df["Band"].unique():
        d = df[df["Band"] == band]
        ax.plot(d["Waktu (UTC)"], d["Mean TBB (°C)"], marker="o", label=band)

    ax.set_ylabel("Mean TBB (°C)")
    ax.set_xlabel("Waktu (UTC)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # =====================================================
    # INTERPRETASI OTOMATIS
    # =====================================================
    min_delta = df["ΔTBB (°C/10m)"].min()

    st.subheader("📝 Kesimpulan Otomatis")

    if min_delta <= -15:
        st.error("🌪️ TERDETEKSI RAPID COOLING EKSTREM – SANGAT KONSISTEN DENGAN PUTING BELIUNG")
    elif min_delta <= -10:
        st.warning("⛈️ RAPID COOLING KUAT – POTENSI CUACA EKSTREM")
    elif min_delta <= -5:
        st.info("🌧️ Pendinginan cepat terdeteksi")
    else:
        st.success("☁️ Tidak terdeteksi pendinginan signifikan")

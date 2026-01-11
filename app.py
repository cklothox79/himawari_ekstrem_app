# =========================================================
# 🛰️ HIMAWARI EXTREME WEATHER ANALYSIS – STAGE 2
# Time Series Mean TBB (B08, B09, B13)
# Author: Ferri Kusuma x ChatGPT
# =========================================================

import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import re

# =========================================================
# KONFIGURASI
# =========================================================
st.set_page_config(page_title="Analisis TBB Himawari", layout="centered")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data_nc"

# =========================================================
# FUNGSI BANTU
# =========================================================
def find_nearest_pixel(lat2d, lon2d, lat0, lon0):
    dist2 = (lat2d - lat0)**2 + (lon2d - lon0)**2
    iy, ix = np.unravel_index(np.argmin(dist2), dist2.shape)
    return iy, ix


def extract_mean_tbb(ds, lat0, lon0, radius_km):
    tbb = ds["tbb"].values
    lat = ds["latitude"].values
    lon = ds["longitude"].values

    # pastikan 2D
    if lat.ndim == 1 and lon.ndim == 1:
        lon2d, lat2d = np.meshgrid(lon, lat)
    else:
        lat2d, lon2d = lat, lon

    iy, ix = find_nearest_pixel(lat2d, lon2d, lat0, lon0)

    # aproksimasi 1 pixel ≈ 2 km
    radius_px = int(radius_km / 2)

    y_min = max(iy - radius_px, 0)
    y_max = min(iy + radius_px, tbb.shape[0])
    x_min = max(ix - radius_px, 0)
    x_max = min(ix + radius_px, tbb.shape[1])

    mean_tbb = np.nanmean(tbb[y_min:y_max, x_min:x_max])

    return mean_tbb - 273.15  # Kelvin → Celsius


def parse_band_time(fname):
    band = re.search(r"B(\d{2})", fname).group(1)
    time = re.search(r"_(\d{12})\.nc", fname).group(1)
    return band, time


# =========================================================
# UI
# =========================================================
st.title("🛰️ Analisis Suhu Puncak Awan (TBB) – Himawari")
st.caption("Tahap 2 – Time Series berbasis koordinat & radius")

lat0 = st.number_input("Lintang (°)", value=-7.3735, format="%.4f")
lon0 = st.number_input("Bujur (°)", value=112.7938, format="%.4f")
radius_km = st.slider("Radius Analisis (km)", 2, 20, 10)

st.write("📂 Folder data_nc:", DATA_DIR)

# =========================================================
# PROSES
# =========================================================
if st.button("▶️ Jalankan Analisis"):
    files = sorted(DATA_DIR.glob("*.nc"))

    if not files:
        st.error("❌ Tidak ada file NC di folder data_nc")
        st.stop()

    records = []

    for f in files:
        try:
            band, time = parse_band_time(f.name)
            ds = xr.open_dataset(f)
            mean_tbb = extract_mean_tbb(ds, lat0, lon0, radius_km)

            records.append({
                "Waktu_UTC": time,
                "Band": f"B{band}",
                "Mean_TBB_C": round(mean_tbb, 2)
            })
        except Exception as e:
            st.warning(f"Gagal proses {f.name}: {e}")

    if not records:
        st.error("❌ Tidak ada data yang berhasil diproses")
        st.stop()

    df = pd.DataFrame(records)
    df["Waktu_UTC"] = pd.to_datetime(df["Waktu_UTC"], format="%Y%m%d%H%M")
    df = df.sort_values("Waktu_UTC")

    st.subheader("📊 Tabel Time Series Mean TBB (°C)")
    st.dataframe(df, use_container_width=True)

    # =====================================================
    # GRAFIK
    # =====================================================
    st.subheader("📈 Grafik Perkembangan TBB")

    fig, ax = plt.subplots()
    for band in df["Band"].unique():
        dfx = df[df["Band"] == band]
        ax.plot(dfx["Waktu_UTC"], dfx["Mean_TBB_C"], marker="o", label=band)

    ax.set_ylabel("Mean TBB (°C)")
    ax.set_xlabel("Waktu (UTC)")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    # =====================================================
    # INTERPRETASI OTOMATIS
    # =====================================================
    st.subheader("📝 Interpretasi Singkat")

    min_tbb = df["Mean_TBB_C"].min()

    if min_tbb < -60:
        st.error("🌪️ Awan Cumulonimbus sangat intens – POTENSI EKSTREM TINGGI")
    elif min_tbb < -50:
        st.warning("⛈️ Awan Cumulonimbus matang – POTENSI CUACA EKSTREM")
    elif min_tbb < -40:
        st.info("🌧️ Awan konvektif berkembang")
    else:
        st.success("☁️ Awan non-konvektif dominan")

    st.caption("Analisis otomatis berbasis TBB Himawari-8")

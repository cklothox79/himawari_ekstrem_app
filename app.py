# =========================================================
#  HIMAWARI-9 EXTREME WEATHER ANALYSIS (FIXED VERSION)
# =========================================================

import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from math import radians, cos, sin, asin, sqrt

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Analisis Cuaca Ekstrem Himawari-9",
    layout="wide"
)

# =========================================================
# FUNCTIONS
# =========================================================
def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(
        radians, [lon1, lat1, lon2, lat2]
    )
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))

def read_nc_safe(file):
    try:
        ds = xr.open_dataset(file, engine="scipy")
        return ds
    except Exception as e:
        st.warning(f"Gagal membaca file {file.name}: {e}")
        return None

def extract_radius_mean(ds, lat0, lon0, radius_km):
    # Koordinat 2D Himawari
    lat2d = ds["latitude"].values
    lon2d = ds["longitude"].values

    # Ambil variable utama (Radiance / TBB)
    var_name = list(ds.data_vars.keys())[0]
    data = ds[var_name].values

    # Hitung jarak
    dist = np.vectorize(haversine)(
        lon0, lat0, lon2d, lat2d
    )

    mask = dist <= radius_km
    if np.sum(mask) == 0:
        return np.nan

    return np.nanmean(data[mask])

# =========================================================
# UI
# =========================================================
st.title("🌪️ Analisis Cuaca Ekstrem Himawari-9")
st.markdown("**Studi Kasus: Puting Beliung Terminal 1 Bandara Juanda**")

with st.sidebar:
    st.header("📍 Lokasi Kejadian")
    lat0 = st.number_input(
        "Latitude", value=-7.373539, format="%.6f"
    )
    lon0 = st.number_input(
        "Longitude", value=112.793786, format="%.6f"
    )

    radius = st.selectbox(
        "Radius Analisis (km)", [5, 10]
    )

    st.header("📂 Upload File NC Himawari")
    uploaded_files = st.file_uploader(
        "Upload B08, B09, B13 (1 jam, interval 10 menit)",
        type=["nc"],
        accept_multiple_files=True
    )

# =========================================================
# PROCESS
# =========================================================
if st.button("🔍 Analisis Data"):

    if not uploaded_files:
        st.error("❌ File NC belum diupload")
        st.stop()

    results = []

    for file in uploaded_files:
        ds = read_nc_safe(file)
        if ds is None:
            continue

        mean_val = extract_radius_mean(
            ds, lat0, lon0, radius
        )

        band = file.name.split("_")[1]

        results.append({
            "File": file.name,
            "Band": band,
            "Radius_km": radius,
            "Mean_Value": mean_val
        })

    if not results:
        st.error("❌ Tidak ada data yang berhasil diproses")
        st.stop()

    df = pd.DataFrame(results)

    # =====================================================
    # OUTPUT
    # =====================================================
    st.subheader("📊 Tabel Hasil Analisis")
    st.dataframe(df, use_container_width=True)

    st.subheader("📈 Grafik Time Series")
    fig, ax = plt.subplots()
    ax.plot(df["File"], df["Mean_Value"], marker="o")
    ax.set_xticklabels(df["File"], rotation=90)
    ax.set_ylabel("Nilai Rata-rata")
    ax.set_title(f"Radius {radius} km")
    st.pyplot(fig)

    st.success("✅ Analisis Himawari berhasil")

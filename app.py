# =========================================================
#  HIMAWARI-9 EXTREME WEATHER ANALYSIS (STAGE 1)
#  Stable for Streamlit Cloud (NO netCDF4)
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
    """Calculate distance (km)"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c

def read_nc_safe(file):
    """Read NC safely using h5netcdf"""
    try:
        ds = xr.open_dataset(file, engine="h5netcdf")
        return ds
    except Exception as e:
        st.warning(f"Gagal membaca file {file.name}: {e}")
        return None

def extract_radius_mean(ds, var, lat0, lon0, radius_km):
    lat = ds['lat'].values
    lon = ds['lon'].values
    data = ds[var].values

    lat2d, lon2d = np.meshgrid(lat, lon, indexing='ij')

    dist = np.vectorize(haversine)(lon0, lat0, lon2d, lat2d)
    mask = dist <= radius_km

    if np.sum(mask) == 0:
        return np.nan

    return np.nanmean(data[mask])

# =========================================================
# UI
# =========================================================
st.title("🌪️ Analisis Cuaca Ekstrem Berbasis Himawari-9")
st.markdown("**Studi Kasus: Puting Beliung Terminal 1 Bandara Juanda**")

with st.sidebar:
    st.header("Input Lokasi")
    lat0 = st.number_input("Latitude", value=-7.373539, format="%.6f")
    lon0 = st.number_input("Longitude", value=112.793786, format="%.6f")
    radius = st.selectbox("Radius Analisis (km)", [5, 10])

    st.header("Upload File NC")
    uploaded_files = st.file_uploader(
        "Upload NC (B08, B09, B13 | 1 Jam | 10 Menit)",
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

        var = list(ds.data_vars.keys())[0]

        mean_val = extract_radius_mean(
            ds, var, lat0, lon0, radius
        )

        results.append({
            "File": file.name,
            "Band": var,
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

    st.subheader("📈 Grafik Nilai Rata-rata")
    fig, ax = plt.subplots()
    ax.plot(df["File"], df["Mean_Value"], marker="o")
    ax.set_xticklabels(df["File"], rotation=90)
    ax.set_ylabel("Nilai")
    ax.set_title(f"Radius {radius} km")
    st.pyplot(fig)

    st.success("✅ Analisis selesai")

import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd

st.set_page_config(
    page_title="Analisis Puting Beliung Himawari-9",
    layout="wide"
)

st.title("🌪️ Analisis Suhu Puncak Awan (Himawari-9)")
st.markdown("**Studi Kasus: Puting Beliung Terminal 1 Bandara Juanda**")

# =====================================================
# INPUT
# =====================================================
with st.sidebar:
    st.header("📍 Lokasi Kejadian")
    lat0 = st.number_input("Latitude", value=-7.373539, format="%.6f")
    lon0 = st.number_input("Longitude", value=112.793786, format="%.6f")

    radius_km = st.selectbox("Radius Analisis (km)", [5, 10])

    st.header("📂 Upload File NC (B13)")
    files = st.file_uploader(
        "Upload file NC Himawari (1 jam, tiap 10 menit)",
        type="nc",
        accept_multiple_files=True
    )

# =====================================================
# FUNCTIONS (AMAN)
# =====================================================
def open_nc(file):
    return xr.open_dataset(file, engine="scipy")

def find_nearest_pixel(lat2d, lon2d, lat0, lon0):
    dist2 = (lat2d - lat0)**2 + (lon2d - lon0)**2
    return np.unravel_index(np.argmin(dist2), dist2.shape)

def extract_mean_tbb(ds, lat0, lon0, radius_km):
    lat2d = ds["latitude"].values
    lon2d = ds["longitude"].values
    tbb = ds["tbb"].values

    iy, ix = find_nearest_pixel(lat2d, lon2d, lat0, lon0)

    # Resolusi Himawari ~2 km
    pixel_radius = int(radius_km / 2)

    y1 = max(0, iy - pixel_radius)
    y2 = min(tbb.shape[0], iy + pixel_radius + 1)
    x1 = max(0, ix - pixel_radius)
    x2 = min(tbb.shape[1], ix + pixel_radius + 1)

    window = tbb[y1:y2, x1:x2]
    return float(np.nanmean(window))

# =====================================================
# PROCESS
# =====================================================
if st.button("🔍 Proses Analisis"):

    if not files:
        st.warning("Silakan upload file NC terlebih dahulu")
        st.stop()

    hasil = []

    for f in files:
        ds = open_nc(f)

        mean_tbb = extract_mean_tbb(
            ds, lat0, lon0, radius_km
        )

        waktu = f.name.split("_")[-1].replace(".nc", "")

        hasil.append({
            "Waktu (UTC)": waktu,
            "Radius (km)": radius_km,
            "Mean TBB (K)": round(mean_tbb, 2),
            "Mean TBB (°C)": round(mean_tbb - 273.15, 2)
        })

    df = pd.DataFrame(hasil).sort_values("Waktu (UTC)")

    st.subheader("📊 Hasil Suhu Puncak Awan")
    st.dataframe(df, use_container_width=True)

    st.success("✅ Analisis berhasil tanpa crash")

# =========================================================
# HIMAWARI-9 EXTREME WEATHER ANALYSIS
# SAFE VERSION FOR STREAMLIT CLOUD
# =========================================================

import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Analisis Cuaca Ekstrem Himawari-9",
    layout="wide"
)

# =========================================================
# SAFE FUNCTIONS
# =========================================================
def open_nc(file):
    try:
        return xr.open_dataset(file, engine="scipy")
    except Exception as e:
        st.error(f"Gagal membuka {file.name}: {e}")
        return None


def find_nearest_pixel(ds, lat0, lon0):
    """
    Cari pixel terdekat dari lokasi kejadian
    Aman untuk berbagai struktur Himawari
    """
    # Cari coordinate latitude & longitude
    for lat_name in ["latitude", "lat"]:
        if lat_name in ds:
            lat = ds[lat_name]
            break
    else:
        raise ValueError("Latitude tidak ditemukan di file")

    for lon_name in ["longitude", "lon"]:
        if lon_name in ds:
            lon = ds[lon_name]
            break
    else:
        raise ValueError("Longitude tidak ditemukan di file")

    # Pastikan 2D
    if lat.ndim == 1 and lon.ndim == 1:
        lon2d, lat2d = np.meshgrid(lon, lat)
    else:
        lat2d = lat.values
        lon2d = lon.values

    dist2 = (lat2d - lat0)**2 + (lon2d - lon0)**2
    iy, ix = np.unravel_index(np.argmin(dist2), dist2.shape)

    return iy, ix


def extract_mean_window(ds, lat0, lon0, radius_km):
    """
    Ambil rata-rata pixel sekitar lokasi
    """
    var_name = list(ds.data_vars.keys())[0]
    data = ds[var_name].values

    iy, ix = find_nearest_pixel(ds, lat0, lon0)

    # Estimasi resolusi Himawari ~2 km
    pixel_radius = int(radius_km / 2)

    y1 = max(0, iy - pixel_radius)
    y2 = min(data.shape[0], iy + pixel_radius)
    x1 = max(0, ix - pixel_radius)
    x2 = min(data.shape[1], ix + pixel_radius)

    window = data[y1:y2, x1:x2]

    return float(np.nanmean(window))


# =========================================================
# UI
# =========================================================
st.title("🌪️ Analisis Cuaca Ekstrem Himawari-9")
st.markdown("**Studi Kasus: Puting Beliung Terminal 1 Bandara Juanda**")

with st.sidebar:
    st.header("📍 Lokasi Kejadian")
    lat0 = st.number_input("Latitude", value=-7.373539, format="%.6f")
    lon0 = st.number_input("Longitude", value=112.793786, format="%.6f")

    radius = st.selectbox("Radius Analisis (km)", [5, 10])

    st.header("📂 Upload File NC")
    files = st.file_uploader(
        "File Himawari B08/B09/B13 (1 jam)",
        type="nc",
        accept_multiple_files=True
    )

# =========================================================
# PROCESS
# =========================================================
if st.button("🔍 Analisis"):

    if not files:
        st.warning("File NC belum diupload")
        st.stop()

    output = []

    for f in files:
        ds = open_nc(f)
        if ds is None:
            continue

        try:
            mean_val = extract_mean_window(
                ds, lat0, lon0, radius
            )
        except Exception as e:
            st.error(f"Gagal proses {f.name}: {e}")
            continue

        band = f.name.split("_")[1]

        output.append({
            "File": f.name,
            "Band": band,
            "Radius_km": radius,
            "Mean_Value": mean_val
        })

    if not output:
        st.error("Tidak ada data berhasil diproses")
        st.stop()

    df = pd.DataFrame(output)

    st.subheader("📊 Tabel Hasil")
    st.dataframe(df, use_container_width=True)

    st.subheader("📈 Grafik Time Series")
    fig, ax = plt.subplots()
    ax.plot(df["File"], df["Mean_Value"], marker="o")
    ax.set_xticklabels(df["File"], rotation=90)
    ax.set_ylabel("Nilai Rata-rata")
    ax.set_title(f"Radius {radius} km")
    st.pyplot(fig)

    st.success("✅ Analisis selesai tanpa crash")

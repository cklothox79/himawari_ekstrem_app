# =====================================================
#  HIMAWARI TBB EXTREME WEATHER ANALYSIS – FINAL STAGE 1
#  Stabil | Anti Oh No Error | BMKG Ready
# =====================================================

import streamlit as st
import numpy as np
import xarray as xr

st.set_page_config(
    page_title="Analisis TBB Himawari",
    layout="centered"
)

st.title("🛰️ Analisis Suhu Puncak Awan (TBB) Himawari")
st.caption("Tahap 1 – Ekstraksi Mean TBB berbasis koordinat")

# =====================================================
#  FUNGSI AMAN & STABIL
# =====================================================

def find_nearest_pixel(lat2d, lon2d, lat0, lon0):
    """
    Cari pixel terdekat dari koordinat target
    Aman untuk MaskedArray / Streamlit Cloud
    """
    lat = np.asarray(lat2d, dtype=float)
    lon = np.asarray(lon2d, dtype=float)

    lat_f = lat.ravel()
    lon_f = lon.ravel()

    dist = np.abs(lat_f - lat0) + np.abs(lon_f - lon0)
    idx = np.nanargmin(dist)

    iy, ix = np.unravel_index(idx, lat.shape)
    return iy, ix


def extract_mean_tbb(ds, lat0, lon0, radius_km):
    """
    Hitung rata-rata TBB di sekitar titik target
    """
    lat2d = ds["latitude"].values
    lon2d = ds["longitude"].values
    tbb = ds["tbb"].values

    iy, ix = find_nearest_pixel(lat2d, lon2d, lat0, lon0)

    # Aproksimasi resolusi Himawari ~2 km
    pixel_radius = max(1, int(radius_km / 2))

    y1 = max(0, iy - pixel_radius)
    y2 = min(tbb.shape[0], iy + pixel_radius + 1)
    x1 = max(0, ix - pixel_radius)
    x2 = min(tbb.shape[1], ix + pixel_radius + 1)

    window = tbb[y1:y2, x1:x2]

    return float(np.nanmean(window))


# =====================================================
#  INPUT PENGGUNA
# =====================================================

st.subheader("📍 Lokasi Kejadian")

lat0 = st.number_input(
    "Lintang (°)",
    value=-7.5,
    step=0.01,
    format="%.4f"
)

lon0 = st.number_input(
    "Bujur (°)",
    value=112.5,
    step=0.01,
    format="%.4f"
)

radius_km = st.slider(
    "Radius Analisis (km)",
    min_value=2,
    max_value=20,
    value=10
)

st.subheader("🧪 Tes Buka File NC Himawari")

uploaded_file = st.file_uploader(
    "Upload 1 file NC Himawari saja",
    type=["nc"]
)

# =====================================================
#  PROSES FILE
# =====================================================

if uploaded_file:
    st.success(f"📂 Nama file: {uploaded_file.name}")

    try:
        ds = xr.open_dataset(uploaded_file)

        st.success("✅ File NC BERHASIL dibuka")

        st.markdown("📌 **Variabel:**")
        st.code(list(ds.data_vars))

        st.markdown("📌 **Koordinat:**")
        st.code(list(ds.coords))

        if "tbb" not in ds:
            st.error("❌ Variabel 'tbb' tidak ditemukan")
            st.stop()

        if "latitude" not in ds.coords or "longitude" not in ds.coords:
            st.error("❌ Koordinat latitude / longitude tidak ditemukan")
            st.stop()

        if st.button("▶️ Proses Analisis TBB"):
            mean_tbb = extract_mean_tbb(
                ds, lat0, lon0, radius_km
            )

            st.subheader("📊 Hasil Analisis")
            st.metric(
                label="Mean TBB (°C)",
                value=f"{mean_tbb:.2f}"
            )

            # Interpretasi cepat
            if mean_tbb <= -60:
                st.error("⚠️ Awan Cumulonimbus sangat tinggi (potensi ekstrem)")
            elif mean_tbb <= -50:
                st.warning("⛈️ Awan konvektif tinggi")
            else:
                st.info("🌤️ Tidak terindikasi awan konvektif kuat")

    except Exception as e:
        st.error("❌ Terjadi kesalahan saat membaca file")
        st.code(str(e))

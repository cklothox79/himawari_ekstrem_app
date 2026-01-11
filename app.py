# =====================================================
#  HIMAWARI TBB EXTREME WEATHER ANALYSIS – FINAL FIX
#  SUPPORT LAT/LON 1D (BMKG STANDARD)
# =====================================================

import streamlit as st
import numpy as np
import xarray as xr

st.set_page_config(
    page_title="Analisis TBB Himawari",
    layout="centered"
)

st.title("🛰️ Analisis Suhu Puncak Awan (TBB) Himawari")
st.caption("Ekstraksi Mean TBB berbasis koordinat (FIXED)")

# =====================================================
#  FUNGSI UTAMA (AMAN 1D GRID)
# =====================================================

def find_nearest_index(arr, value):
    arr = np.asarray(arr, dtype=float)
    return int(np.nanargmin(np.abs(arr - value)))


def extract_mean_tbb(ds, lat0, lon0, radius_km):
    """
    Hitung mean TBB berbasis lat/lon 1D Himawari
    """
    lat = ds["latitude"].values
    lon = ds["longitude"].values
    tbb = ds["tbb"].values

    iy = find_nearest_index(lat, lat0)
    ix = find_nearest_index(lon, lon0)

    # Resolusi Himawari ~2 km
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
#  PROSES
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

        if not all(v in ds for v in ["tbb"]):
            st.error("❌ Variabel 'tbb' tidak ditemukan")
            st.stop()

        if not all(c in ds.coords for c in ["latitude", "longitude"]):
            st.error("❌ Koordinat latitude / longitude tidak ditemukan")
            st.stop()

        if st.button("▶️ Proses Analisis TBB"):
            mean_tbb = extract_mean_tbb(
                ds, lat0, lon0, radius_km
            )

            st.subheader("📊 Hasil Analisis")
            st.metric("Mean TBB (°C)", f"{mean_tbb:.2f}")

            # Interpretasi BMKG
            if mean_tbb <= -60:
                st.error("⚠️ Awan Cumulonimbus sangat tinggi (Cuaca Ekstrem)")
            elif mean_tbb <= -50:
                st.warning("⛈️ Awan konvektif tinggi")
            else:
                st.info("🌤️ Tidak terindikasi awan konvektif signifikan")

    except Exception as e:
        st.error("❌ Terjadi kesalahan")
        st.code(str(e))

# =========================================================
#  APP.PY – TAHAP 1
#  ANALISIS CUACA EKSTREM HIMAWARI (NC FILE)
#  Radius 5 km & 10 km | Tabel + Grafik
# =========================================================

import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from math import radians, cos, sin, asin, sqrt

# =========================================================
#  KONFIGURASI HALAMAN
# =========================================================
st.set_page_config(
    page_title="Analisis Cuaca Ekstrem Himawari",
    layout="wide"
)

st.title("🌩️ Analisis Cuaca Ekstrem Berbasis Satelit Himawari")
st.caption("Studi Kasus: Puting Beliung Bandara Juanda – 8 Januari 2026")

# =========================================================
#  FUNGSI UTILITAS
# =========================================================
def haversine(lon1, lat1, lon2, lat2):
    """
    Hitung jarak antara dua titik (km)
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r


def extract_radius_stats(ds, lon0, lat0, radius_km):
    """
    Ekstraksi statistik dalam radius tertentu
    """
    lats = ds['latitude'].values
    lons = ds['longitude'].values
    tbb = ds['tbb'].values - 273.15  # K → °C

    lon2d, lat2d = np.meshgrid(lons, lats)
    dist = haversine(lon0, lat0, lon2d, lat2d)

    mask = dist <= radius_km
    data = tbb[mask]

    return {
        "min": float(np.nanmin(data)),
        "mean": float(np.nanmean(data))
    }


# =========================================================
#  SIDEBAR INPUT
# =========================================================
st.sidebar.header("🔧 Input Analisis")

lat0 = st.sidebar.number_input(
    "Latitude Lokasi Kejadian",
    value=-7.373539,
    format="%.6f"
)

lon0 = st.sidebar.number_input(
    "Longitude Lokasi Kejadian",
    value=112.793786,
    format="%.6f"
)

uploaded_files = st.sidebar.file_uploader(
    "Upload File NC (1 jam, resolusi 10 menit)",
    type=["nc"],
    accept_multiple_files=True
)

process = st.sidebar.button("🚀 Proses Analisis")

# =========================================================
#  PROSES UTAMA
# =========================================================
if process and uploaded_files:

    st.success("File berhasil diunggah. Memproses data...")

    results = []

    for file in uploaded_files:
        ds = xr.open_dataset(file)

        # Ambil waktu dari metadata
        time_str = ds.attrs.get("start_time", None)
        if time_str:
            waktu = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        else:
            waktu = file.name[-16:-3]  # fallback nama file

        stats_5 = extract_radius_stats(ds, lon0, lat0, 5)
        stats_10 = extract_radius_stats(ds, lon0, lat0, 10)

        results.append({
            "Waktu": waktu,
            "CTT Min 5 km (°C)": stats_5["min"],
            "CTT Mean 5 km (°C)": stats_5["mean"],
            "CTT Min 10 km (°C)": stats_10["min"],
            "CTT Mean 10 km (°C)": stats_10["mean"]
        })

    df = pd.DataFrame(results).sort_values("Waktu")

    # =====================================================
    #  TABEL HASIL
    # =====================================================
    st.subheader("📊 Tabel Ringkasan Suhu Puncak Awan (CTT)")
    st.dataframe(df, use_container_width=True)

    # =====================================================
    #  GRAFIK TIME SERIES
    # =====================================================
    st.subheader("📈 Time Series Suhu Puncak Awan")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df["Waktu"], df["CTT Min 5 km (°C)"], marker="o", label="Min 5 km")
    ax.plot(df["Waktu"], df["CTT Min 10 km (°C)"], marker="s", label="Min 10 km")

    ax.set_ylabel("CTT (°C)")
    ax.set_xlabel("Waktu UTC")
    ax.set_title("Perkembangan Suhu Puncak Awan")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    # =====================================================
    #  INTERPRETASI OTOMATIS (VERSI AWAL)
    # =====================================================
    st.subheader("🧠 Interpretasi Awal Otomatis")

    min_10 = df["CTT Min 10 km (°C)"].min()
    trend = df["CTT Min 10 km (°C)"].iloc[-1] - df["CTT Min 10 km (°C)"].iloc[0]

    if min_10 <= -60:
        fase = "Awan Cumulonimbus sangat kuat"
    elif min_10 <= -50:
        fase = "Awan konvektif kuat"
    else:
        fase = "Awan konvektif sedang"

    narasi = f"""
    Teramati suhu puncak awan minimum hingga {min_10:.1f}°C pada radius 10 km
    dari lokasi kejadian. Pola perubahan suhu puncak awan menunjukkan
    {'penurunan signifikan' if trend < 0 else 'fluktuasi terbatas'},
    yang mengindikasikan proses konveksi aktif.
    Kondisi ini konsisten dengan keberadaan {fase}
    yang berpotensi menimbulkan cuaca ekstrem seperti angin kencang
    atau puting beliung.
    """

    st.write(narasi)

else:
    st.info("⬅️ Silakan upload file NC dan klik **Proses Analisis**")

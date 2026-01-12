# ============================================================
#  HIMAWARI-8 MULTI BAND EXTREME WEATHER ANALYSIS
#  Puting Beliung Detection – BMKG Style
#  Author: Ferri Kusuma + ChatGPT
# ============================================================

import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# ============================================================
# KONFIGURASI
# ============================================================
DATA_DIR = Path("data_nc")
BANDS = ["B07", "B08", "B09", "B10", "B13", "B15"]

st.set_page_config(
    page_title="Analisis Puting Beliung – Himawari-8",
    layout="wide"
)

# ============================================================
# FUNGSI DASAR
# ============================================================
def load_band_timeseries(band):
    files = sorted((DATA_DIR / band).glob("*.nc"))
    data = []
    times = []

    for f in files:
        try:
            ds = xr.open_dataset(f)
            tbb = ds["tbb"]
            lat = ds["latitude"].values
            lon = ds["longitude"].values

            time_str = f.stem.split("_")[-1]
            time = datetime.strptime(time_str, "%Y%m%d%H%M")

            data.append((tbb, lat, lon))
            times.append(time)
        except:
            continue

    return data, times


def mean_radius_tbb(tbb, lat, lon, lat0, lon0, radius_km):
    lat2d, lon2d = np.meshgrid(lat, lon, indexing="ij")
    dist_km = np.sqrt(
        (lat2d - lat0)**2 + (lon2d - lon0)**2
    ) * 111.0

    mask = dist_km <= radius_km
    return float(np.nanmean(tbb.values[mask]))


# ============================================================
# SIDEBAR INPUT
# ============================================================
st.sidebar.title("📍 Lokasi & Parameter")

lat0 = st.sidebar.number_input("Lintang (°)", value=-7.3735, format="%.4f")
lon0 = st.sidebar.number_input("Bujur (°)", value=112.7938, format="%.4f")
radius_km = st.sidebar.slider("Radius Analisis (km)", 2, 20, 5)

st.sidebar.markdown("---")
st.sidebar.info("Data diambil otomatis dari folder data_nc")

# ============================================================
# LOAD DATA
# ============================================================
band_data = {}
band_times = {}

for band in BANDS:
    data, times = load_band_timeseries(band)
    if len(data) == 0:
        st.error(f"Tidak ada data valid untuk {band}")
        st.stop()
    band_data[band] = data
    band_times[band] = times

# gunakan waktu dari B13 sebagai referensi
times = band_times["B13"]

# ============================================================
# HITUNG TIME SERIES
# ============================================================
rows = []

for i, t in enumerate(times):
    try:
        values = {}
        for band in BANDS:
            tbb, lat, lon = band_data[band][i]
            values[band] = mean_radius_tbb(
                tbb, lat, lon, lat0, lon0, radius_km
            )

        row = {
            "Time": t,
            **values
        }
        rows.append(row)
    except:
        continue

df = pd.DataFrame(rows)
df.set_index("Time", inplace=True)

# ============================================================
# HITUNG INDEKS
# ============================================================
df["Updraft_Index"] = df["B07"] - df["B13"]
df["Rapid_Cooling"] = df["B13"].diff()
df["Dry_Intrusion"] = df["B10"].diff()
df["Turbulence"] = abs(df["B13"] - df["B15"])

# ============================================================
# LOGIKA PUTING BELIUNG
# ============================================================
def classify(row):
    if row["Updraft_Index"] <= -5 and (
        row["Rapid_Cooling"] <= -3 or row["Dry_Intrusion"] >= 1.5
    ):
        return "🌪️ POTENSI PUTING BELIUNG"
    elif row["Updraft_Index"] <= -5:
        return "⛈️ KONVEKSI KUAT LOKAL"
    else:
        return "🌤️ KONVEKSI BIASA"

df["Kesimpulan"] = df.apply(classify, axis=1)

# ============================================================
# TAMPILAN UTAMA
# ============================================================
st.title("🌪️ Analisis Puting Beliung – Himawari-8 (Multi Band)")
st.caption("Berbasis TBB, Updraft, Rapid Cooling, Dry Intrusion")

st.subheader("📊 Tabel Time Series")
st.dataframe(df.round(2), use_container_width=True)

# ============================================================
# GRAFIK
# ============================================================
st.subheader("📈 Grafik Indeks Utama")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df.index, df["Updraft_Index"], label="Updraft Index")
ax.plot(df.index, df["Rapid_Cooling"], label="Rapid Cooling")
ax.plot(df.index, df["Dry_Intrusion"], label="Dry Intrusion")
ax.axhline(-5, linestyle="--", alpha=0.5)
ax.legend()
ax.set_ylabel("Nilai Indeks")
ax.grid(True)

st.pyplot(fig)

# ============================================================
# KESIMPULAN OTOMATIS
# ============================================================
st.subheader("📝 Kesimpulan Otomatis")

final_status = df["Kesimpulan"].value_counts().idxmax()
st.success(final_status)

st.markdown(
    """
**Catatan:**
- Sistem ini menggabungkan *updraft awal*, *pendinginan puncak awan*,
  dan *intrusi udara kering*.
- Cocok untuk kejadian puting beliung tropis skala lokal.
"""
)

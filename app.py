import os
import numpy as np
import pandas as pd
import xarray as xr
import streamlit as st
import matplotlib.pyplot as plt
from scipy.ndimage import distance_transform_edt

# ===============================
# KONFIGURASI
# ===============================
DATA_DIR = "data_nc"
BANDS = ["B07", "B08", "B09", "B10", "B13", "B15"]

# ===============================
# FUNGSI UTILITAS
# ===============================
def open_nc_safe(path):
    try:
        return xr.open_dataset(path)
    except Exception:
        return None

def extract_mean_tbb(ds, lat0, lon0, radius_km):
    lat = ds["latitude"].values
    lon = ds["longitude"].values
    tbb = ds["tbb"].values

    if lat.ndim == 1 and lon.ndim == 1:
        lon2d, lat2d = np.meshgrid(lon, lat)
    else:
        lat2d, lon2d = lat, lon

    # jarak kasar (km)
    dist = np.sqrt((lat2d - lat0)**2 + (lon2d - lon0)**2) * 111
    mask = dist <= radius_km

    if np.sum(mask) == 0:
        return np.nan

    return np.nanmean(tbb[mask])

def read_band_timeseries(folder, lat, lon, radius):
    records = []
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".nc"):
            continue
        ds = open_nc_safe(os.path.join(folder, f))
        if ds is None or "tbb" not in ds:
            continue

        mean_tbb = extract_mean_tbb(ds, lat, lon, radius)
        time = f.split("_")[-1].replace(".nc", "")
        records.append((time, mean_tbb))

    return pd.DataFrame(records, columns=["time", "tbb"])

def rapid_cooling(df):
    if len(df) < 2:
        return 0
    return df["tbb"].diff().min()

# ===============================
# STREAMLIT UI
# ===============================
st.set_page_config(layout="wide")
st.title("🌪️ Deteksi Dini Puting Beliung – Himawari-8")
st.caption("Rapid Cooling | Composite Index | Operasional BMKG")

lat0 = st.number_input("Lintang (°)", value=-7.37, format="%.4f")
lon0 = st.number_input("Bujur (°)", value=112.79, format="%.4f")
radius = st.slider("Radius Analisis (km)", 2, 20, 5)

# ===============================
# PROSES DATA
# ===============================
band_results = {}
cooling_scores = []

for band in BANDS:
    folder = os.path.join(DATA_DIR, band)
    if not os.path.exists(folder):
        continue

    df = read_band_timeseries(folder, lat0, lon0, radius)
    if df.empty:
        continue

    band_results[band] = df
    cooling = rapid_cooling(df)
    cooling_scores.append(cooling)

# ===============================
# OUTPUT
# ===============================
if not band_results:
    st.error("❌ Tidak ada data yang berhasil diproses")
    st.stop()

st.subheader("📊 Time Series TBB")
for band, df in band_results.items():
    st.markdown(f"**{band}**")
    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots()
    ax.plot(df["time"], df["tbb"], marker="o")
    ax.set_ylabel("TBB (°C)")
    ax.set_xlabel("Waktu")
    ax.set_title(f"TBB {band}")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# ===============================
# ANALISIS OTOMATIS
# ===============================
min_cooling = np.nanmin(cooling_scores)

st.subheader("🧠 Analisis Otomatis")

if min_cooling <= -12:
    level = "🚨 SANGAT KUAT"
elif min_cooling <= -8:
    level = "⚠️ KUAT"
elif min_cooling <= -4:
    level = "WASPADA"
else:
    level = "LEMAH"

st.markdown(f"""
### 🌪️ Kesimpulan
- **Rapid Cooling Minimum:** `{min_cooling:.2f} °C / 10 menit`
- **Level Ancaman:** **{level}**
""")

# ===============================
# NARASI BMKG OTOMATIS
# ===============================
st.subheader("📝 Narasi Otomatis BMKG")

narasi = f"""
**ANALISIS CUACA EKSTREM BERBASIS HIMAWARI-8**

Berdasarkan analisis citra satelit Himawari-8 kanal inframerah, terpantau adanya
**pendinginan suhu puncak awan (rapid cooling)** yang signifikan di sekitar
koordinat **({lat0:.3f}, {lon0:.3f})** dengan radius analisis ±{radius} km.

Nilai penurunan TBB maksimum mencapai **{min_cooling:.2f}°C dalam interval 10 menit**,
mengindikasikan pertumbuhan awan konvektif yang cepat dan intens.

Kondisi ini menunjukkan keberadaan awan **Cumulonimbus aktif** yang berpotensi
menimbulkan **cuaca ekstrem berupa hujan lebat disertai angin kencang hingga puting beliung**.
"""

st.text_area("Narasi Siap Pakai", narasi, height=260)

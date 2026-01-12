# =========================================================
#  HIMAWARI-8 EXTREME WEATHER ANALYSIS (MULTI-BAND)
#  Final Stable Version
# =========================================================

import os
import numpy as np
import pandas as pd
import xarray as xr
import streamlit as st
import matplotlib.pyplot as plt

# =========================================================
#  KONFIGURASI APP
# =========================================================
st.set_page_config(
    page_title="Analisis Puting Beliung – Himawari-8",
    layout="wide"
)

st.title("🌪️ Analisis Puting Beliung – Himawari-8 (Multi-Band)")
st.caption("Berbasis TBB | Radius | Time Series | Operasional BMKG")

# =========================================================
#  INPUT LOKASI
# =========================================================
col1, col2, col3 = st.columns(3)

with col1:
    lat0 = st.number_input("Lintang (°)", value=-7.3735, format="%.4f")

with col2:
    lon0 = st.number_input("Bujur (°)", value=112.7938, format="%.4f")

with col3:
    radius_km = st.slider("Radius Analisis (km)", 2, 20, 5)

DATA_DIR = "data_nc"

# =========================================================
#  FUNGSI EKSTRAK MEAN TBB (FINAL)
# =========================================================
def mean_tbb_radius(ds, lat0, lon0, radius_km):
    # Ambil variabel TBB
    if "tbb" in ds:
        tbb = ds["tbb"].values
    else:
        tbb = list(ds.data_vars.values())[0].values

    lat = ds["latitude"].values
    lon = ds["longitude"].values

    # Cari pixel terdekat
    iy = np.abs(lat - lat0).argmin()
    ix = np.abs(lon - lon0).argmin()

    # Resolusi IR Himawari ~2 km
    res_km = 2.0
    pix = max(1, int(radius_km / res_km))

    y0 = max(0, iy - pix)
    y1 = min(tbb.shape[0], iy + pix + 1)
    x0 = max(0, ix - pix)
    x1 = min(tbb.shape[1], ix + pix + 1)

    sub = tbb[y0:y1, x0:x1]

    if sub.size < 5:
        return np.nan

    return float(np.nanmean(sub))

# =========================================================
#  PROSES MULTI-BAND
# =========================================================
bands = ["B07", "B08", "B09", "B10", "B13", "B15"]
results = []

st.subheader("📂 Status Folder Data")

for band in bands:
    folder = os.path.join(DATA_DIR, band)

    if not os.path.exists(folder):
        st.error(f"{band} ❌ folder tidak ditemukan")
        continue

    files = sorted([f for f in os.listdir(folder) if f.endswith(".nc")])

    if len(files) == 0:
        st.warning(f"{band} ❌ tidak ada file")
        continue

    st.success(f"{band} ✅ {len(files)} file ditemukan")

    for f in files:
        path = os.path.join(folder, f)
        try:
            ds = xr.open_dataset(path)
            mean_tbb = mean_tbb_radius(ds, lat0, lon0, radius_km)

            results.append({
                "Band": band,
                "File": f,
                "Mean_TBB_K": mean_tbb
            })

        except Exception as e:
            st.warning(f"{band} | {f} ❌ {e}")

# =========================================================
#  HASIL
# =========================================================
st.divider()
st.subheader("📊 Hasil Analisis Multi-Band")

df = pd.DataFrame(results)

if len(df) == 0:
    st.error("❌ Tidak ada data yang berhasil diproses")
    st.stop()

df["Mean_TBB_C"] = df["Mean_TBB_K"] - 273.15
st.dataframe(df, use_container_width=True)

# =========================================================
#  GRAFIK TIME SERIES PER BAND
# =========================================================
st.subheader("📈 Time Series Mean TBB")

fig, ax = plt.subplots(figsize=(10, 5))

for band in bands:
    sub = df[df["Band"] == band]
    if len(sub) > 0:
        ax.plot(sub.index, sub["Mean_TBB_C"], marker="o", label=band)

ax.set_ylabel("Mean TBB (°C)")
ax.set_xlabel("Index Waktu (10-menitan)")
ax.legend()
ax.grid(True)

st.pyplot(fig)

# =========================================================
#  INTERPRETASI OTOMATIS SEDERHANA
# =========================================================
st.subheader("📝 Interpretasi Otomatis")

cooling = df.groupby("Band")["Mean_TBB_C"].agg(["max", "min"])
cooling["ΔTBB"] = cooling["max"] - cooling["min"]

st.dataframe(cooling)

if (cooling["ΔTBB"] > 8).any():
    st.success("🌪️ Indikasi kuat awan konvektif intens / puting beliung")
else:
    st.info("🌧️ Konveksi terdeteksi, namun tanpa pendinginan ekstrem")

st.caption("Analisis berbasis Himawari-8 | BMKG-style | Tahap Operasional")

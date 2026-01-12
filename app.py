# =========================================================
#  HIMAWARI-8 PUTING BELIUNG ANALYSIS – OPERATIONAL VERSION
# =========================================================

import os
import numpy as np
import pandas as pd
import xarray as xr
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Deteksi Puting Beliung – Himawari-8",
    layout="wide"
)

st.title("🌪️ Deteksi Dini Puting Beliung – Himawari-8")
st.caption("Rapid Cooling Rate | Composite Index | Operasional BMKG")

# =========================================================
# INPUT LOKASI
# =========================================================
c1, c2, c3 = st.columns(3)
with c1:
    lat0 = st.number_input("Lintang (°)", value=-7.37, format="%.4f")
with c2:
    lon0 = st.number_input("Bujur (°)", value=112.79, format="%.4f")
with c3:
    radius_km = st.slider("Radius Analisis (km)", 2, 20, 5)

DATA_DIR = "data_nc"

# =========================================================
# FUNGSI MEAN TBB
# =========================================================
def mean_tbb(ds, lat0, lon0, radius_km):
    tbb = list(ds.data_vars.values())[0].values
    lat = ds["latitude"].values
    lon = ds["longitude"].values

    iy = np.abs(lat - lat0).argmin()
    ix = np.abs(lon - lon0).argmin()

    pix = max(1, int(radius_km / 2.0))  # resolusi IR ~2 km

    sub = tbb[
        max(0, iy - pix):iy + pix + 1,
        max(0, ix - pix):ix + pix + 1
    ]

    return float(np.nanmean(sub))

# =========================================================
# PROSES DATA
# =========================================================
bands = ["B07", "B08", "B09", "B10", "B13", "B15"]
rows = []

for band in bands:
    folder = os.path.join(DATA_DIR, band)
    if not os.path.exists(folder):
        continue

    for f in sorted(os.listdir(folder)):
        if not f.endswith(".nc"):
            continue

        ds = xr.open_dataset(os.path.join(folder, f))
        tbb_k = mean_tbb(ds, lat0, lon0, radius_km)

        rows.append({
            "Band": band,
            "File": f,
            "TBB_C": tbb_k - 273.15
        })

df = pd.DataFrame(rows)

if df.empty:
    st.error("❌ Data tidak terbaca")
    st.stop()

# =========================================================
# RAPID COOLING RATE (FOKUS IR)
# =========================================================
ir_df = df[df["Band"].isin(["B13", "B15"])].copy()
ir_df["ΔTBB"] = ir_df.groupby("Band")["TBB_C"].diff()

# =========================================================
# COMPOSITE INDEX PUTING BELIUNG (CIPI)
# =========================================================
cipi = (
    (-ir_df["ΔTBB"].clip(lower=-15, upper=0) / 15) * 0.5 +
    (-(ir_df["TBB_C"] + 80).clip(lower=0) / 80) * 0.5
)

ir_df["CIPI"] = cipi.clip(0, 1)

# =========================================================
# TAMPILAN DATA
# =========================================================
st.subheader("📊 Data TBB & Rapid Cooling")
st.dataframe(ir_df, use_container_width=True)

# =========================================================
# GRAFIK
# =========================================================
st.subheader("📉 Rapid Cooling Rate")

fig, ax = plt.subplots()
for band in ["B13", "B15"]:
    sub = ir_df[ir_df["Band"] == band]
    ax.plot(sub.index, sub["ΔTBB"], marker="o", label=band)

ax.axhline(-4, linestyle="--")
ax.axhline(-8, linestyle="--")
ax.axhline(-12, linestyle="--")
ax.set_ylabel("ΔTBB (°C / 10 menit)")
ax.legend()
ax.grid()
st.pyplot(fig)

# =========================================================
# INTERPRETASI OPERASIONAL
# =========================================================
st.subheader("🧠 Interpretasi Operasional")

min_cooling = ir_df["ΔTBB"].min()
max_cipi = ir_df["CIPI"].max()

if min_cooling <= -12 and max_cipi > 0.75:
    st.error("🚨 AWAS: Indikasi KUAT PUTING BELIUNG")
elif min_cooling <= -8:
    st.warning("⚠️ SIAGA: Konveksi eksplosif berpotensi puting beliung")
elif min_cooling <= -4:
    st.info("🌧️ WASPADA: Awan konvektif aktif")
else:
    st.success("☁️ Kondisi relatif stabil")

st.caption("Algoritma operasional berbasis Himawari-8 | BMKG")

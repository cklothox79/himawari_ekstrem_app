import streamlit as st
import xarray as xr

st.set_page_config(page_title="NC TEST", layout="centered")
st.title("🧪 Tes Buka File NC Himawari")

uploaded = st.file_uploader(
    "Upload 1 file NC Himawari saja",
    type="nc"
)

if uploaded:
    st.write("📂 Nama file:", uploaded.name)

    try:
        ds = xr.open_dataset(uploaded, engine="scipy")
        st.success("✅ File NC BERHASIL dibuka")

        st.write("📌 Variabel:")
        st.write(list(ds.data_vars))

        st.write("📌 Koordinat:")
        st.write(list(ds.coords))

    except Exception as e:
        st.error("❌ Gagal membuka file NC")
        st.exception(e)

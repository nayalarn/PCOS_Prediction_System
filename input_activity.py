import streamlit as st
import pandas as pd
import numpy as np
import datetime
import joblib
import os

from database import conn, c


 
# SESSION
 
if "history" not in st.session_state:
    st.session_state.history = []

if "selected_mood" not in st.session_state:
    st.session_state.selected_mood = "🤔"


 
# LOAD DATA
 
@st.cache_data
def load_data():

    file_path = "dataset_pi.xlsx"

    if not os.path.exists(file_path):
        return None, None, None

    df_makan = pd.read_excel(
        file_path,
        sheet_name="food",
        header=2
    )

    df_olahraga = pd.read_excel(
        file_path,
        sheet_name="exercise"
    )

    df_minum = pd.read_excel(
        file_path,
        sheet_name="drink"
    )

    return df_makan, df_olahraga, df_minum


df_makan, df_olahraga, df_minum = load_data()

 
# PAGE
 
def input_activity_page():

    st.title("Input Aktivitas")

    st.write("---")

    col1, col2 = st.columns([2, 2.5])

    kalori_item = 0
    gula_item = 0
    air_minum = 0

    item_list = []
    porsi = {}

    durasi_tidur = "-"

     
    # INPUT AKTIVITAS
     
    with col1:

        st.subheader("Aktivitas")

        tgl = st.date_input(
            "tanggal",
            datetime.date.today(),
            format="DD/MM/YYYY"
        )

        jam_default = datetime.datetime.now().replace(
            second=0,
            microsecond=0
        ).time()

        jam = st.time_input(
            "Jam",
            value=jam_default
        )

        aktivitas = st.selectbox(

            "Aktivitas",

            [
                "Makan",
                "Minum",
                "Olahraga",
                "Istirahat",
                "Tidur"
            ],

            index=None
        )

         
        # MAKAN
        
        if aktivitas == "Makan" and df_makan is not None:

            menu = (
                df_makan.iloc[:, 0]
                .dropna()
                .tolist()
            )

            item_list = st.multiselect(
                "Menu Makan",
                menu
            )

            for i in item_list:

                porsi[i] = st.number_input(
                    f"Porsi {i}",
                    0.5,
                    10.0,
                    1.0,
                    0.5,
                    key=i
                )

                row = df_makan[
                    df_makan.iloc[:, 0] == i
                ]

                if not row.empty:

                    kal = pd.to_numeric(
                        row.iloc[0, 2],
                        errors="coerce"
                    )

                    kal = (
                        0
                        if np.isnan(kal)
                        else kal
                    )

                    kalori_item += (
                        kal * porsi[i]
                    )

                    gul = pd.to_numeric(
                        row.iloc[0, 6],
                        errors="coerce"
                    )

                    gul = (
                        0
                        if np.isnan(gul)
                        else gul
                    )

                    gula_item += (
                        gul * porsi[i]
                    )

         
        # MINUM
         
        elif aktivitas == "Minum" and df_minum is not None:

            drink = st.selectbox(
                "Minuman",
                df_minum.iloc[:, 0]
                .dropna()
                .tolist()
            )

            item_list = [drink]

            if "air putih" in drink.lower():
                jumlah = st.number_input(
                    "Jumlah Gelas",
                    1,
                    20,
                    1
                )

                gula = 0

                # 1 gelas = 250 ml
                air_minum = jumlah * 0.25

            else:

                jumlah = st.number_input(
                    "Jumlah",
                    1,
                    10,
                    1
                )

                if (
                    "kopi" in drink.lower()
                    or
                    "teh" in drink.lower()
                    or
                    "kelapa" in drink.lower()
                ):

                    gula = st.number_input(
                        "Tambahan Gula (sdm)",
                        0,
                        10,
                        0
                    )

                else:

                    gula = 0

            porsi[drink] = jumlah

            row = df_minum[
                df_minum.iloc[:, 0] == drink
            ]

            if not row.empty:

                base_kalori = pd.to_numeric(
                    row.iloc[0, 1],
                    errors="coerce"
                )

                base_kalori = (
                    0
                    if np.isnan(base_kalori)
                    else base_kalori
                )

                base_gula = pd.to_numeric(
                    row.iloc[0, 6],
                    errors="coerce"
                )

                base_gula = (
                    0
                    if np.isnan(base_gula)
                    else base_gula
                )

                kalori_item = (
                    (
                        base_kalori
                        +
                        (gula * 16)
                    )
                    *
                    jumlah
                )

                gula_item = (
                    (
                        base_gula
                        +
                        (gula * 12)
                    )
                    *
                    jumlah
                )

         
        # OLAHRAGA
         
        elif aktivitas == "Olahraga" and df_olahraga is not None:

            sport = st.selectbox(
                "Olahraga",
                df_olahraga.iloc[:, 0]
                .dropna()
                .tolist()
            )

            durasi = st.number_input(
                "Durasi (menit)",
                5,
                180,
                15
            )

            item_list = [sport]

            porsi[sport] = durasi

            row = df_olahraga[
                df_olahraga.iloc[:, 0] == sport
            ]

            if not row.empty:

                kal = pd.to_numeric(
                    row.iloc[0, 1],
                    errors="coerce"
                )

                kal = (
                    0
                    if np.isnan(kal)
                    else kal
                )

                kalori_item = -(
                    kal * durasi
                )

         
        # ISTIRAHAT
         
        elif aktivitas == "Istirahat":

            awal = st.time_input("Dari")
            akhir = st.time_input("Hingga")

            durasi = (
                datetime.datetime.combine(tgl, akhir)
                -
                datetime.datetime.combine(tgl, awal)
            ).seconds / 3600

            item_list = ["Istirahat"]

            porsi["Istirahat"] = durasi

            st.info(
                f"Durasi istirahat: {durasi:.1f} jam"
            )

         
        # TIDUR
         
        elif aktivitas == "Tidur":

            tidur = st.time_input(
                "Jam Tidur"
            )

            bangun = st.time_input(
                "Jam Bangun"
            )

            start = datetime.datetime.combine(
                tgl,
                tidur
            )

            end = datetime.datetime.combine(
                tgl,
                bangun
            )

            if end < start:

                end += datetime.timedelta(days=1)

            durasi = (
                end - start
            ).seconds / 3600

            durasi_tidur = durasi

            item_list = ["Tidur"]

            porsi["Tidur"] = durasi

            st.info(
                f"Durasi tidur: {durasi:.1f} jam"
            )

     
    # MOOD
     
    with col2:

        st.subheader("🩸 Kondisi & Mood")

        status_haid = st.radio(

            "Status Menstruasi",

            [
                "Tidak Menstruasi",
                "Sedang Menstruasi"
            ],

            horizontal=True
        )

        h_ke = 0

        if status_haid == "Sedang Menstruasi":

            h_ke = st.slider(
                "Hari ke-",
                1,
                35,
                1
            )

        moods = [
            "🤩 Bahagia",
            "😐 Standar",
            "🥲 Sedih",
            "😡 Stress"
        ]

        cols = st.columns(2)

        for i, m in enumerate(moods):

            if cols[i % 2].button(m):

                st.session_state.selected_mood = m

        st.info(
            f"Mood: {st.session_state.selected_mood}"
        )

         
        # SAVE DATA
         
        if st.button(
            "SIMPAN DATA",
            type="primary"
        ):

            if not item_list:

                st.error(
                    "Pilih aktivitas dulu!"
                )

                return

            for item in item_list:
                tanggal_val = tgl.strftime("%d-%m-%Y")
                tanggal_db = tgl.strftime("%Y-%m-%d")
                waktu_val = str(jam)
                aktivitas_val = aktivitas
                item_val = item
                jumlah_val = porsi[item]
                mood_val = st.session_state.selected_mood
                kalori_val = round(kalori_item, 1)
                gula_val = round(gula_item, 1)
                air_minum_val = round(air_minum, 2) if aktivitas == "Minum" else 0.0
                durasi_tidur_val = round(durasi_tidur, 1) if aktivitas == "Tidur" else 0.0
                jam_tidur_val = str(tidur) if aktivitas == "Tidur" else "-"
                haid_val = f"Ya (H-{h_ke})" if status_haid == "Sedang Menstruasi" else "Tidak"

                # SAVE TO SQLITE DATABASE FIRST
                c.execute("""
                    INSERT INTO activity_history (
                        user_id, tanggal, waktu, aktivitas, item, jumlah, mood, 
                        kalori, gula, air_minum, durasi_tidur, jam_tidur, haid
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    st.session_state.user_id,
                    tanggal_db,
                    waktu_val,
                    aktivitas_val,
                    item_val,
                    jumlah_val,
                    mood_val,
                    kalori_val,
                    gula_val,
                    air_minum_val,
                    str(durasi_tidur_val),
                    jam_tidur_val,
                    haid_val
                ))
                inserted_id = c.lastrowid

                # SAVE TO SESSION STATE WITH THE NEW SQLITE ID
                st.session_state.history.append({
                    "id": inserted_id,
                    "tanggal": tanggal_val,
                    "Waktu": waktu_val,
                    "Aktivitas": aktivitas_val,
                    "Item": item_val,
                    "Jumlah": jumlah_val,
                    "Mood": mood_val,
                    "Est. Kalori (Kal)": kalori_val,
                    "Est. Gula (g)": gula_val,
                    "Air Minum (L)": air_minum_val,
                    "Durasi Tidur": durasi_tidur_val,
                    "Jam Tidur": jam_tidur_val,
                    "Haid": haid_val,
                })
            conn.commit()

            st.success("Data berhasil disimpan!")
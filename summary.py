import streamlit as st
import pandas as pd
import datetime
import numpy as np


def summary_page():

    st.title("Ringkasan Aktivitas")
    st.write("---")

    if "history" not in st.session_state or len(st.session_state.history) == 0:
        st.info("Belum ada data aktivitas")
        return

    df = pd.DataFrame(st.session_state.history)

    # SAFE COLUMN
    default_cols = {
        "tanggal": str(datetime.date.today()),
        "Est. Kalori (Kal)": 0,
        "Est. Gula (g)": 0,
        "Durasi Tidur": 0,
        "Air Minum (L)": 0
    }

    for col, val in default_cols.items():
        if col not in df.columns:
            df[col] = val

    df["tanggal"] = pd.to_datetime(
        df["tanggal"],
        dayfirst=True,
        errors="coerce"
    )

    today = pd.Timestamp(datetime.date.today())
    df["tanggal"] = df["tanggal"].fillna(today)

    # CONVERT NUMERIC
    numeric_cols = [
        "Est. Kalori (Kal)",
        "Est. Gula (g)",
        "Durasi Tidur",
        "Air Minum (L)"
    ]

    for col in numeric_cols:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        ).fillna(0)

    # FILTER
    harian = df[df["tanggal"].dt.date == today.date()]
    mingguan = df[df["tanggal"].dt.date >= (today - pd.Timedelta(days=7)).date()]
    bulanan = df[df["tanggal"].dt.date >= (today - pd.Timedelta(days=30)).date()]

    # TARGET
    TARGET_KALORI_HARI = 2000
    TARGET_GULA_HARI = 25
    TARGET_TIDUR_HARI = 8
    TARGET_AIR_HARI = 2

    TARGET_KALORI_MINGGU = TARGET_KALORI_HARI * 7
    TARGET_GULA_MINGGU = TARGET_GULA_HARI * 7
    TARGET_TIDUR_MINGGU = TARGET_TIDUR_HARI * 7
    TARGET_AIR_MINGGU = TARGET_AIR_HARI * 7

    TARGET_KALORI_BULAN = TARGET_KALORI_HARI * 30
    TARGET_GULA_BULAN = TARGET_GULA_HARI * 30
    TARGET_TIDUR_BULAN = TARGET_TIDUR_HARI * 30
    TARGET_AIR_BULAN = TARGET_AIR_HARI * 30

    # ANALYZE
    def analyze(data, target_kal, target_gula, target_tidur, target_air):

        kal = pd.to_numeric(
            data["Est. Kalori (Kal)"],
            errors="coerce"
        ).fillna(0).sum()

        gula = pd.to_numeric(
            data["Est. Gula (g)"],
            errors="coerce"
        ).fillna(0).sum()

        tidur = pd.to_numeric(
            data["Durasi Tidur"],
            errors="coerce"
        ).fillna(0).sum()

        air = pd.to_numeric(
            data["Air Minum (L)"],
            errors="coerce"
        ).fillna(0).sum()

        # GAP
        gap_kal = kal - target_kal
        gap_gula = gula - target_gula
        gap_tidur = tidur - target_tidur
        gap_air = air - target_air

        # STATUS
        def get_status(gap, normal_limit):

            if abs(gap) <= normal_limit:
                return "Normal"

            elif gap > normal_limit:
                return "Berlebih"

            else:
                return "Kurang"

        status_kal = get_status(gap_kal, 200)
        status_gula = get_status(gap_gula, 10)
        status_tidur = get_status(gap_tidur, 1)
        status_air = get_status(gap_air, 0.5)

        return {
            "kal": kal,
            "gula": gula,
            "tidur": tidur,
            "air": air,
            "gap_kal": gap_kal,
            "gap_gula": gap_gula,
            "gap_tidur": gap_tidur,
            "gap_air": gap_air,
            "status_kal": status_kal,
            "status_gula": status_gula,
            "status_tidur": status_tidur,
            "status_air": status_air
        }

    # ANALYSIS
    h = analyze(
        harian,
        TARGET_KALORI_HARI,
        TARGET_GULA_HARI,
        TARGET_TIDUR_HARI,
        TARGET_AIR_HARI
    )

    m = analyze(
        mingguan,
        TARGET_KALORI_MINGGU,
        TARGET_GULA_MINGGU,
        TARGET_TIDUR_MINGGU,
        TARGET_AIR_MINGGU
    )

    b = analyze(
        bulanan,
        TARGET_KALORI_BULAN,
        TARGET_GULA_BULAN,
        TARGET_TIDUR_BULAN,
        TARGET_AIR_BULAN
    )

    # DISPLAY
    def render(title, data):

        st.subheader(title)

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.metric(
                "Kalori",
                f"{data['kal']:.1f}",
                f"{data['gap_kal']:+.1f}"
            )

        with c2:
            st.metric(
                "Gula",
                f"{data['gula']:.1f}",
                f"{data['gap_gula']:+.1f}"
            )

        with c3:
            st.metric(
                "Tidur",
                f"{data['tidur']:.1f} jam",
                f"{data['gap_tidur']:+.1f}"
            )

        with c4:
            st.metric(
                "Air",
                f"{data['air']:.1f} L",
                f"{data['gap_air']:+.1f}"
            )

        # INSIGHT
        if data["status_tidur"] == "Kurang":
            st.warning("Durasi tidur kamu masih kurang 😴")

        if data["status_air"] == "Kurang":
            st.warning("Kurang minum air putih 💧")

        st.write("---")

    # RENDER
    render("📅 Harian", h)
    render("📆 Mingguan", m)
    render("📊 Bulanan", b)


    # TREND TIDUR
    st.subheader("😴 Trend Tidur")

    trend_tidur = df.groupby(
        df["tanggal"].dt.date
    )["Durasi Tidur"].sum()

    st.line_chart(trend_tidur)
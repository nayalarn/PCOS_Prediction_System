import streamlit as st
import pandas as pd
import datetime
import joblib
import numpy as np

# LOAD MODEL
@st.cache_resource
def load_model():
    try:
        model = joblib.load("pcos_model.pkl")
        scaler = joblib.load("scaler.pkl")
        return model, scaler
    except:
        return None, None

model_ai, scaler = load_model()

# BULAN INDONESIA
bulan_indo = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

# DASHBOARD PAGE
def dashboard_page():
    from database import c

    # STYLE METRIC DAN WARNING
    st.html(
        """
        <style>
        [data-testid="stMetricLabel"] p { font-size: 24px !important; font-weight: 600 !important; white-space: nowrap !important; }
        [data-testid="stMetricValue"] > div { font-size: 24px !important; }
        [data-testid="stCallout"] p, [data-testid="stCallout"] div,
        [data-testid="stNotification"] p, [data-testid="stNotification"] div { font-size: 28px !important; }
        </style>
        """
    )

    # AMBIL PROFILE
    c.execute(
        "SELECT nama, weight, height, cycle_length, last_period FROM profile WHERE user_id=?",
        (st.session_state.user_id,)
    )
    profile = c.fetchone()

    if profile:
        nama_user = profile[0]
        berat = profile[1]
        tinggi = profile[2]
        cycle_length = profile[3]
        last_period = profile[4]
    else:
        nama_user = st.session_state.username
        berat, tinggi, cycle_length, last_period = None, None, None, None

    # HEADER
    now = datetime.datetime.now()
    tanggal_indo = f"{now.day} {bulan_indo[now.month]} {now.year}"

    st.title(f"🌿 Halo, Kak {nama_user}")
    st.markdown(f"### 📅 {tanggal_indo}\n### ⏰ {now.strftime('%H:%M')} WIB")
    st.write("---")

    # BMI
    bmi = None
    kategori_bmi = "-"
    if berat and tinggi:
        tinggi_m = tinggi / 100
        bmi = berat / (tinggi_m ** 2)
        if bmi < 18.5: kategori_bmi = "Kurus"
        elif bmi < 25: kategori_bmi = "Normal"
        elif bmi < 30: kategori_bmi = "Gemuk"
        else: kategori_bmi = "Obesitas"

    # HITUNG NEXT PERIOD
    next_period = "-"
    late_days = 0
    if cycle_length and last_period:
        try:
            last_period_date = pd.to_datetime(last_period).date() if isinstance(last_period, str) else last_period
            next_date = last_period_date + datetime.timedelta(days=int(cycle_length))
            next_period = f"{next_date.day} {bulan_indo[next_date.month]} {next_date.year}"
            today = datetime.date.today()
            if today > next_date:
                late_days = (today - next_date).days
        except:
            pass

    # HISTORY
    if "history" not in st.session_state:
        st.session_state.history = []

    total_data = len(st.session_state.history)
    total_kalori = 0
    total_gula = 0
    total_air = 0
    mood_hari_ini = "-"
    durasi_tidur = 0
    jam_tidur_malam = False
    menstruasi = "-"

    if total_data > 0:
        df_temp = pd.DataFrame(st.session_state.history)

        # --- PERBAIKAN NAMA KOLOM (Disamakan dengan activity.py) ---
        required_columns = [
            "Est. Kalori (Kal)",
            "Est. Gula (g)",
            "Durasi Tidur",
            "Air Minum (L)",
            "Mood",
            "Haid",
            "Item",
            "Jumlah",
            "Aktivitas",
            "Jam Tidur"
        ]

        for col in required_columns:
            if col not in df_temp.columns:
                df_temp[col] = 0 if "Est." in col or "Air" in col or "Durasi" in col else "-"

        # Ambil data HARI INI saja agar relevan dengan Dashboard Harian
        df_temp["tanggal_dt"] = pd.to_datetime(df_temp["tanggal"], format="mixed", errors="coerce").dt.date
        df_today = df_temp[df_temp["tanggal_dt"] == datetime.date.today()]

        if not df_today.empty:
            # KALORI & GULA
            total_kalori = pd.to_numeric(df_today["Est. Kalori (Kal)"], errors="coerce").fillna(0).sum()
            total_gula = pd.to_numeric(df_today["Est. Gula (g)"], errors="coerce").fillna(0).sum()

            # AIR PUTIH (Dihitung dari total Air Minum (L) dikali 4 untuk konversi ke Gelas, 1 Gelas = 0.25 L)
            total_air = pd.to_numeric(df_today["Air Minum (L)"], errors="coerce").fillna(0).sum() * 4

            # MOOD & HAID (Mengambil baris terakhir hari ini)
            mood_hari_ini = df_today["Mood"].iloc[-1]
            menstruasi = df_today["Haid"].iloc[-1]

            # TIDUR
            total_tidur = pd.to_numeric(df_today["Durasi Tidur"], errors="coerce").fillna(0).sum()
            if total_tidur > 0:
                durasi_tidur = total_tidur

            # JAM TIDUR
            tidur_data = df_today[df_today["Aktivitas"] == "Tidur"]
            if not tidur_data.empty:
                jam_tidur = tidur_data["Jam Tidur"].iloc[-1]
                try:
                    jam_tidur_obj = datetime.datetime.strptime(str(jam_tidur), "%H:%M:%S").time()
                    if jam_tidur_obj.hour >= 23 or jam_tidur_obj.hour < 5:
                        jam_tidur_malam = True
                except:
                    pass

    # REKOMENDASI
    st.markdown("## Rekomendasi Harian")
    if total_air < 8:
        st.warning("💧 Minum air putih masih kurang dari 8 gelas.")
    else:
        st.success("✅ Konsumsi air putih sudah cukup.")

    if total_gula > 50:
        st.warning("🍭 Konsumsi gula cukup tinggi hari ini.")
    else:
        st.success("✅ Konsumsi gula masih normal.")

    if total_kalori > 2200:
        st.warning("🔥 Kalori harian cukup tinggi.")
    elif total_kalori < 1200 and total_kalori != 0:
        st.warning("⚠️ Kalori harian terlalu rendah.")
    else:
        st.success("✅ Kalori harian cukup seimbang.")

    if durasi_tidur != 0:
        if durasi_tidur < 7: st.warning("😴 Durasi tidur kurang dari 7 jam.")
        elif durasi_tidur > 9: st.warning("🛌 Durasi tidur terlalu lama.")
        else: st.success("✅ Durasi tidur ideal.")

    if jam_tidur_malam:
        st.warning("🌙 Kamu tidur terlalu malam.")

    st.divider()

    # STATUS UTAMA
    st.markdown("## Status Utama")
    c1, c2, c3, c4, = st.columns(4)
    with c1: st.metric("BMI", f"{bmi:.2f}" if bmi else "-")
    with c2: st.metric("Kategori BMI", kategori_bmi)
    with c3:
        score = max(0, 100 - (total_kalori / 30)) if total_kalori > 0 else 100
        st.metric("Skor Gaya Hidup", f"{score:.0f}")
    with c4: st.metric("Menstruasi Selanjutnya", next_period)

    st.divider()

    # NUTRISI
    st.markdown("## Nutrisi Harian")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Aktivitas", total_data)
    with c2: st.metric("Kalori", f"{total_kalori:.1f} Kal")
    with c3: st.metric("Gula", f"{total_gula:.1f} g")
    with c4: st.metric("Air Putih", f"{total_air:.0f} gelas")

    st.divider()

    # PEMULIHAN
    st.markdown("## Pemulihan & Monitoring")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Tidur", f"{durasi_tidur:.1f} jam" if durasi_tidur != 0 else "-")
    with c2: st.metric("Mood", mood_hari_ini)
    with c3: st.metric("Menstruasi", menstruasi)
    st.divider()
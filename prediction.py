import streamlit as st
import pandas as pd
import numpy as np
import joblib
import datetime
import altair as alt

from database import c, conn


# LOAD MODEL
@st.cache_resource
def load_model():
    model = joblib.load("model_pcos_final.pkl")
    imputer = joblib.load("imputer.pkl")
    scaler = joblib.load("scaler.pkl")
    model_info = joblib.load("model_pcos_info.pkl")
    return model, imputer, scaler, model_info

model, imputer, scaler, model_info = load_model()
final_features = model_info['features']
final_threshold = model_info['threshold']


# HITUNG RISIKO
def hitung_risiko_pcos(probability):
    if probability < 0.30:
        return "Rendah"
    elif probability < 0.60:
        return "Sedang"
    else:
        return "Tinggi"


# PREDICTION PAGE
def prediction_page():
    st.markdown(
        """
        <style>
        [data-testid="stMetricLabel"] p {
            font-size: 24px !important;
            font-weight: 600 !important;
            white-space: nowrap !important;
        }
        [data-testid="stMetricValue"] > div {
            font-size: 24px !important;
        }
        [data-testid="stCallout"] p, [data-testid="stCallout"] div,
        [data-testid="stNotification"] p, [data-testid="stNotification"] div {
            font-size: 28px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("Hasil Prediksi PCOS (Polycystic Ovary Syndrome)")
    st.write("---")

    # ==================== AMBIL DATA PROFILE + FITUR BARU ====================
    c.execute(
        """
        SELECT
            weight, height, cycle_length, last_period, age, waist, hip,
            weight_gain, hair_growth, skin_darkening, hair_loss, pimples, fast_food, reg_exercise
        FROM profile
        WHERE user_id=?
        """,
        (st.session_state.user_id,)
    )
    data = c.fetchone()

    # VALIDASI DATA AWAL
    if not data:
        st.warning("⚠️ Data profile belum diisi. Silakan isi data diri Anda terlebih dahulu.")
        st.stop()

    # Unpack data dari query database
    (weight, height, cycle_length, last_period, age, waist, hip,
     weight_gain, hair_growth, skin_darkening, hair_loss, pimples, fast_food, reg_exercise) = data

    if not weight or not height or not cycle_length:
        st.warning("Lengkapi data berat badan, tinggi badan, dan siklus menstruasi di profile terlebih dahulu!")
        st.stop()

    # ==================== KALKULASI VARIABEL ====================
    # BMI & Rasio Pinggang-Pinggul
    bmi = weight / ((height / 100) ** 2)
    wh_ratio = waist / hip if (hip and hip > 0) else 0.0

    # Menghitung Keterlambatan Menstruasi
    late_days = 0
    next_period = None

    if last_period:
        try:
            # Mengatasi perbedaan format tanggal dari DB (str atau date object)
            if isinstance(last_period, str):
                try:
                    last_period_date = pd.to_datetime(last_period, format="%Y-%m-%d").date()
                except ValueError:
                    last_period_date = pd.to_datetime(last_period, format="%d-%m-%Y").date()
            else:
                last_period_date = last_period.date() if hasattr(last_period, "date") else last_period

            next_period = last_period_date + datetime.timedelta(days=int(cycle_length))
            today = datetime.date.today()

            if today > next_period:
                late_days = (today - next_period).days
        except Exception as e:
            pass

    # ==================== MAPPING INPUT UNTUK MODEL MACHINE LEARNING ====================
    # Mengubah string 'Y'/'N' menjadi numerik 1/0 agar bisa dibaca model ML
    map_yn = {"Y": 1, "N": 0}
    
    # Sesuaikan susunan kolom ini dengan urutan fitur saat kamu men-train model ML (pcos_model.pkl)
    input_features = {
        "Age (yrs)": age,
        "Weight (Kg)": weight,
        "Height(Cm)": height,
        "BMI": bmi,
        "Cycle length(days)": cycle_length,
        "Weight gain(Y/N)": map_yn.get(weight_gain, 0),
        "hair growth(Y/N)": map_yn.get(hair_growth, 0),
        "Skin darkening (Y/N)": map_yn.get(skin_darkening, 0),
        "Hair loss(Y/N)": map_yn.get(hair_loss, 0),
        "Pimples(Y/N)": map_yn.get(pimples, 0),
        "Fast food (Y/N)": map_yn.get(fast_food, 0),
        "Reg.Exercise(Y/N)": map_yn.get(reg_exercise, 0),
        "Waist(inch)": waist,
        "Hip(inch)": hip,
        "Waist:Hip Ratio": wh_ratio
    }
    
    input_data = pd.DataFrame([input_features])

    # SCALING & PREDIKSI
    try:
        required_features = model_info["features"]
        input_data = input_data[required_features]

        X_imp = imputer.transform(input_data)
        X_scaled = scaler.transform(X_imp)
        probability = model.predict_proba(X_scaled)[0][1]

    except Exception as e:
        st.error(
            f"Terjadi ketidakcocokan data input dengan model.\n\nError: {e}"
        )
        probability = 0.0

    threshold = model_info["threshold"]

    status = (
        "Berisiko PCOS"
        if probability >= threshold
        else "Tidak Berisiko PCOS"
    )

    risiko = hitung_risiko_pcos(probability)

    # ==================== DISPLAY HALAMAN UTAMA ====================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Probabilitas", f"{probability:.2%}")

    with col2:
        st.metric("Kategori", risiko)

    with col3:
        st.metric("Prediksi", status)

    # PENJELASAN PCOS
    with st.expander("ℹ️ Tentang PCOS"):
        st.write(
            """
            PCOS (Polycystic Ovary Syndrome) atau Sindrom Ovarium Polikistik merupakan gangguan hormonal yang umum terjadi pada wanita usia reproduksi akibat ketidakseimbangan hormon yang memengaruhi fungsi ovarium dan proses ovulasi. Kondisi ini dapat ditandai dengan siklus menstruasi yang tidak teratur, pertumbuhan rambut berlebih, jerawat, peningkatan berat badan, serta gangguan kesuburan. Selain memengaruhi kesehatan reproduksi, PCOS juga berkaitan dengan peningkatan risiko resistensi insulin, diabetes melitus tipe 2, dan penyakit kardiovaskular. Melalui aplikasi ini, pengguna dapat melakukan prediksi risiko PCOS berdasarkan data kesehatan yang dimiliki serta memantau aktivitas harian sebagai upaya mendukung deteksi dini dan penerapan gaya hidup sehat.
            """
            
        )

    # ANALISIS INDIKATOR
    st.subheader("Analisis Risiko")
    col_a, col_b = st.columns(2)
    
    with col_a:
        if bmi >= 25:
            st.warning(f"⚠️ BMI Anda ({bmi:.1f}) di atas normal.")
        else:
            st.success(f"✅ BMI Anda ({bmi:.1f}) dalam rentang normal.")

        if cycle_length > 35 or cycle_length < 21:
            st.warning("⚠️ Siklus menstruasi tidak teratur (Abnormal).")
        else:
            st.success("✅ Siklus menstruasi terpantau normal.")
            
    with col_b:
        if late_days >= 7:
            st.error(f"🚨 Menstruasi terlambat {late_days} hari.")
        elif next_period:
            st.success("✅ Siklus haid masih sesuai perkiraan.")
            
        if wh_ratio >= 0.85:
            st.warning(f"⚠️ Rasio Pinggang:Pinggul ({wh_ratio:.2f}) tinggi. Waspada penumpukan lemak perut.")
        else:
            st.success(f"✅ Rasio Pinggang:Pinggul ({wh_ratio:.2f}) aman.")

    # ANALISIS MENSTRUASI & BMI KATEGORI
    st.subheader("Analisis Menstruasi & Tubuh")
    if next_period:
        st.info(f"📆 Perkiraan menstruasi berikutnya: **{next_period.strftime('%d %B %Y')}**")
    
    # Tampilkan info gejala fisik jika ada 'Y'
    gejala_terdeteksi = [k for k, v in {"Jerawat": pimples, "Rambut rontok": hair_loss, "Pertumbuhan rambut wajah": hair_growth, "Penggelapan kulit": skin_darkening}.items() if v == "Y"]
    if gejala_terdeteksi:
        st.warning(f"🔍 Gejala fisik terdeteksi: {', '.join(gejala_terdeteksi)}")

    # GRAFIK KESEHATAN (Altair)
    st.subheader("Grafik Kesehatan")
    chart_data = pd.DataFrame({
        "Kategori": ["BMI", "Risk %", "Cycle Length", "Late Days", "Waist:Hip x100"],
        "Nilai": [bmi, probability * 100, cycle_length, late_days, wh_ratio * 100]
    })

    lines = alt.Chart(chart_data).mark_line(point=True).encode(
        x=alt.X("Kategori:N", sort=None, axis=alt.Axis(domain=True, domainColor="#555555", domainWidth=2)),
        y=alt.Y("Nilai:Q", axis=alt.Axis(domain=True, domainColor="#555555", domainWidth=2))
    )
    labels = lines.mark_text(align='center', baseline='bottom', dy=-10).encode(text=alt.Text('Nilai:Q', format='.1f'))
    st.altair_chart(lines + labels, use_container_width=True)

    # SARAN KESEHATAN
    st.subheader("Saran Kesehatan")
    suggestions = []

    if bmi >= 25 or fast_food == "Y":
        suggestions.append("Kurangi makanan tinggi gula, karbohidrat olahan, dan *fast food*.")
    if reg_exercise == "N":
        suggestions.append("Mulailah berolahraga secara teratur, minimal berjalan kaki 30 menit sehari.")
    if probability >= 0.5 or cycle_length > 35:
        suggestions.append("Disarankan untuk berkonsultasi dengan Dokter Spesialis Kandungan (Sp.OG) untuk pemeriksaan USG transvaginal.")
    
    suggestions.append("Pastikan tidur cukup (7-8 jam) guna membantu menstabilkan hormon tubuh.")

    for s in suggestions:
        st.info(s)

    # DETAIL DATA
    with st.expander("📋 Detail Data yang Digunakan Model"):
        st.json(input_data.iloc[0].to_dict())
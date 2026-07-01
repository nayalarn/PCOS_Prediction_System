import streamlit as st
import datetime

from database import conn, c

def profile_page():
    st.markdown("""
    <style>
    /* INPUT WRAPPER */
    div[data-baseweb="base-input"] {
        background-color: white !important;
        border-radius: 12px !important;
    }

    /* INPUT DALAM */
    div[data-baseweb="base-input"] input {
        background-color: white !important;
    }

    /* SELECTBOX */
    div[data-baseweb="select"] > div {
        background-color: white !important;
        border-radius: 12px !important;
    }

    /* DATE INPUT */
    div[data-baseweb="input"] > div {
        background-color: white !important;
    }

    /* HILANGKAN BIRU DEFAULT */
    [data-baseweb] {
        box-shadow: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Data Diri & Indikator Kesehatan")
    st.write("---")

    # Ambil Data Lama dari Database (Menambahkan kolom-kolom baru)
    c.execute(
        """
        SELECT 
            nama, birth_date, weight, height, cycle_length, 
            period_days, last_period, waist, hip,
            weight_gain, hair_growth, skin_darkening, hair_loss,
            pimples, fast_food, reg_exercise
        FROM profile 
        WHERE user_id=?
        """,
        (st.session_state.user_id,)
    )
    profile = c.fetchone()

    # Inisialisasi Default Nilai
    if profile:
        nama_default = profile[0]

        try:
            if isinstance(profile[1], str):
                birth_default = datetime.datetime.strptime(profile[1], "%Y-%m-%d").date()
            else:
                birth_default = profile[1]
        except (ValueError, TypeError):
            birth_default = datetime.date(2004, 1, 1)
            
        weight_default = profile[2]
        height_default = profile[3]
        cycle_default = profile[4]
        period_default = profile[5]

        try:
            if isinstance(profile[6], str):
                last_default = datetime.datetime.strptime(profile[6], "%Y-%m-%d").date()
            else:
                last_default = profile[6]
        except (ValueError, TypeError):
            last_default = datetime.date.today()

        waist_default = profile[7]
        hip_default = profile[8]
        
        # Fitur Baru Default dari DB
        wg_default = profile[9] if profile[9] in ["Y", "N"] else "N"
        hg_default = profile[10] if profile[10] in ["Y", "N"] else "N"
        sd_default = profile[11] if profile[11] in ["Y", "N"] else "N"
        hl_default = profile[12] if profile[12] in ["Y", "N"] else "N"
        p_default = profile[13] if profile[13] in ["Y", "N"] else "N"
        ff_default = profile[14] if profile[14] in ["Y", "N"] else "N"
        ex_default = profile[15] if profile[15] in ["Y", "N"] else "N"

    else:
        # Default data awal jika user baru
        nama_default = ""
        birth_default = datetime.date(2004, 1, 1) 
        weight_default = 50
        height_default = 160
        cycle_default = 28
        period_default = 7
        last_default = datetime.date.today()
        waist_default = 20
        hip_default = 30
        
        # Fitur baru default awal
        wg_default = "N"
        hg_default = "N"
        sd_default = "N"
        hl_default = "N"
        p_default = "N"
        ff_default = "N"
        ex_default = "N"

    # ==================== INPUT KOMPONEN UI ====================
    
    nama = st.text_input("Nama", value=nama_default)

    st.text_input("Jenis Kelamin", value="Perempuan", disabled=True)

    # Tanggal Lahir (Format Indonesia)
    st.write("**Tanggal Lahir**")
    list_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    list_tahun = list(range(1950, datetime.date.today().year + 1))

    col_tgl, col_bln, col_thn = st.columns(3)
    with col_tgl:
        default_tgl = birth_default.day
        tanggal = st.selectbox("Tanggal", list(range(1, 32)), index=min(default_tgl - 1, 30))
    with col_bln:
        default_bln = birth_default.month - 1
        bulan_nama = st.selectbox("Bulan", list_bulan, index=default_bln)
        bulan_angka = list_bulan.index(bulan_nama) + 1
    with col_thn:
        default_thn = birth_default.year
        try: thn_index = list_tahun.index(default_thn)
        except ValueError: thn_index = 0
        tahun = st.selectbox("Tahun", list_tahun, index=thn_index)

    # Validasi Tanggal Lahir
    try:
        birth_date = datetime.date(tahun, bulan_angka, tanggal)
    except ValueError:
        st.error("⚠️ Kombinasi Tanggal Lahir tidak valid. Silakan koreksi tanggal Anda.")
        st.stop()

    # Hitung Umur Otomatis
    today = datetime.date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    st.text_input("Umur (Age)", value=f"{age} Tahun", disabled=True)

    # Antropometri dasar
    height = st.number_input("Tinggi Badan (Height dalam Cm)", min_value=50, max_value=220, value=int(height_default))
    weight = st.number_input("Berat Badan (Weight dalam Kg)", min_value=0, max_value=250, value=int(weight_default))

    # ---- KALKULASI OTOMATIS: BMI ----
    height_m = height / 100
    bmi = round(weight / (height_m ** 2), 2) if height_m > 0 else 0.0
    st.text_input("BMI (Body Mass Index)", value=str(bmi), disabled=True)

    # Siklus Menstruasi
    cycle = st.number_input("Siklus Menstruasi (Cycle length dalam hari)", min_value=1, max_value=90, value=int(cycle_default))
    period = st.number_input("Lama Menstruasi (hari)", min_value=1, max_value=15, value=int(period_default))

    last_period = st.date_input(
        "Tanggal Hari Pertama Menstruasi Terakhir", 
        value=last_default,
        max_value=datetime.date.today(),
        format="DD/MM/YYYY"     
    )
    
    waist = st.number_input("Ukuran Pinggang (Waist dalam inch)", min_value=0, max_value=100, value=int(waist_default))
    hip = st.number_input("Ukuran Pinggul (Hip dalam inch)", min_value=0, max_value=100, value=int(hip_default))

    # ---- KALKULASI OTOMATIS: Waist to Hip Ratio ----
    wh_ratio = round(waist / hip, 2) if hip > 0 else 0.0
    st.text_input("Waist:Hip Ratio", value=str(wh_ratio), disabled=True)

    # ==================== FITUR BARU: GEJALA & GAYA HIDUP ====================
    st.write("### Kesehatan & Gejala")
    
    options = ["N", "Y"] # N = No, Y = Yes
    
    weight_gain = st.selectbox("Apakah Anda mengalami kenaikan berat badan drastis? (Weight gain)", options, index=options.index(wg_default))
    hair_growth = st.selectbox("Apakah tumbuh rambut berlebih di area wajah/tubuh? (Hair growth/Hirsutism)", options, index=options.index(hg_default))
    skin_darkening = st.selectbox("Apakah ada penggelapan kulit di area lipatan leher/ketiak? (Skin darkening)", options, index=options.index(sd_default))
    hair_loss = st.selectbox("Apakah Anda mengalami kerontokan rambut kepala yang parah? (Hair loss)", options, index=options.index(hl_default))
    pimples = st.selectbox("Apakah Anda berjerawat parah/meradang? (Pimples)", options, index=options.index(p_default))
    fast_food = st.selectbox("Apakah Anda sering mengonsumsi Makanan Cepat Saji? (Fast food)", options, index=options.index(ff_default))
    reg_exercise = st.selectbox("Apakah Anda berolahraga secara teratur? (Reg. Exercise)", options, index=options.index(ex_default))

    # ==================== SIMPAN DATA ====================
    if st.button("Simpan Profile", use_container_width=True):
        c.execute("DELETE FROM profile WHERE user_id=?", (st.session_state.user_id,))

        # Memasukkan semua data lama + data kalkulasi + data fitur baru ke DB
        c.execute("""
        INSERT INTO profile (
            user_id, nama, gender, birth_date, age,
            weight, height, bmi, cycle_length, period_days,
            last_period, waist, hip, waist_hip_ratio,
            weight_gain, hair_growth, skin_darkening, hair_loss,
            pimples, fast_food, reg_exercise
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            st.session_state.user_id,
            nama,
            "Perempuan",
            str(birth_date), 
            age,
            weight,
            height,
            bmi,         
            cycle,
            period,
            str(last_period),
            waist,
            hip,
            wh_ratio,   
            weight_gain, 
            hair_growth, 
            skin_darkening, 
            hair_loss,
            pimples, 
            fast_food, 
            reg_exercise
        ))

        conn.commit()
        st.success("Profile berhasil disimpan!")
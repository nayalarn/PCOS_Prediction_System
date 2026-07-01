import sqlite3

conn = sqlite3.connect(
    "pcos_app.db",
    check_same_thread=False
)

c = conn.cursor()

# 1. TABLE USERS
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# 2. TABLE PROFILE (Sudah diperbarui dengan kolom baru)
c.execute("""
CREATE TABLE IF NOT EXISTS profile (
    user_id INTEGER PRIMARY KEY,
    nama TEXT,
    gender TEXT,
    birth_date TEXT,
    age INTEGER,
    weight REAL,
    height REAL,
    bmi REAL,
    cycle_length INTEGER,
    period_days INTEGER,
    last_period TEXT,
    waist INTEGER,
    hip INTEGER,
    waist_hip_ratio REAL,
    weight_gain TEXT,
    hair_growth TEXT,
    skin_darkening TEXT,
    hair_loss TEXT,
    pimples TEXT,
    fast_food TEXT,
    reg_exercise TEXT
)
""")
conn.commit()

# 3. TABLE ACTIVITY
c.execute("""
CREATE TABLE IF NOT EXISTS activity_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    tanggal TEXT,
    waktu TEXT,
    aktivitas TEXT,
    item TEXT,
    jumlah REAL,
    mood TEXT,
    kalori REAL,
    gula REAL,
    air_minum REAL,
    durasi_tidur TEXT,
    jam_tidur TEXT,
    haid TEXT
)
""")
conn.commit()


# ==================== MIGRATION SYSTEM ====================
# Bagian ini mendeteksi otomatis jika ada kolom baru yang belum masuk ke database lama

def tambah_kolom_jika_belum_ada(nama_kolom, tipe_data, default_value):
    try:
        c.execute(f"SELECT {nama_kolom} FROM profile LIMIT 1")
    except sqlite3.OperationalError:
        try:
            c.execute(f"ALTER TABLE profile ADD COLUMN {nama_kolom} {tipe_data} DEFAULT {default_value}")
            conn.commit()
            print(f"Berhasil menambahkan kolom: {nama_kolom}")
        except Exception as e:
            print(f"Gagal menambahkan kolom {nama_kolom}: {e}")

# Migrasi untuk kolom lama kamu
tambah_kolom_jika_belum_ada("waist", "INTEGER", "0")
tambah_kolom_jika_belum_ada("hip", "INTEGER", "0")

# Migrasi untuk FITUR BARU kalkulasi
tambah_kolom_jika_belum_ada("bmi", "REAL", "0.0")
tambah_kolom_jika_belum_ada("waist_hip_ratio", "REAL", "0.0")

# Migrasi untuk FITUR BARU indikator gejala PCOS (Y/N)
tambah_kolom_jika_belum_ada("weight_gain", "TEXT", "'N'")
tambah_kolom_jika_belum_ada("hair_growth", "TEXT", "'N'")
tambah_kolom_jika_belum_ada("skin_darkening", "TEXT", "'N'")
tambah_kolom_jika_belum_ada("hair_loss", "TEXT", "'N'")
tambah_kolom_jika_belum_ada("pimples", "TEXT", "'N'")
tambah_kolom_jika_belum_ada("fast_food", "TEXT", "'N'")
tambah_kolom_jika_belum_ada("reg_exercise", "TEXT", "'N'")
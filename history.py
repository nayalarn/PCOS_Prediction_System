import streamlit as st
import datetime
import pandas as pd
from database import conn, c

def on_table_change():
    # Ambil perubahan dari editor
    editor_state = st.session_state.history_editor
    edited_rows = editor_state.get("edited_rows", {})
    deleted_rows = editor_state.get("deleted_rows", [])
    
    if not edited_rows and not deleted_rows:
        return
        
    # Buat DataFrame pencocokan dari data riwayat saat ini sebelum diubah
    df_hist = pd.DataFrame(st.session_state.history)
    
    # Penghapusan Baris
    if deleted_rows:
        for row_idx in deleted_rows:
            if row_idx < len(df_hist):
                item_id = df_hist.iloc[row_idx]["id"]
                c.execute("DELETE FROM activity_history WHERE id = ? AND user_id = ?", (int(item_id), st.session_state.user_id))
        conn.commit()

    # Pengeditan Data Baris
    if edited_rows:
        for row_idx_str, edits in edited_rows.items():
            row_idx = int(row_idx_str)
            if row_idx < len(df_hist):
                item_id = df_hist.iloc[row_idx]["id"]

                # Gabungkan data lama dengan data baru yang diedit
                original = df_hist.iloc[row_idx].to_dict()
                updated = {**original, **edits}

                # Konversi tanggal tampilan (DD-MM-YYYY) kembali ke format database (YYYY-MM-DD)
                try:
                    tgl_db = datetime.datetime.strptime(str(updated["tanggal"]), "%d-%m-%Y").strftime("%Y-%m-%d")
                except:
                    tgl_db = str(updated["tanggal"])

                # Simpan ke Database
                c.execute("""
                    UPDATE activity_history
                    SET tanggal=?, waktu=?, item=?, jumlah=?, mood=?, kalori=?, gula=?, air_minum=?, durasi_tidur=?, jam_tidur=?, haid=?
                    WHERE id=? AND user_id=?
                """, (
                    tgl_db,
                    str(updated["Waktu"]),
                    str(updated["Item"]),
                    float(updated["Jumlah"]),
                    str(updated["Mood"]),
                    float(updated["Est. Kalori (Kal)"]),
                    float(updated["Est. Gula (g)"]),
                    float(updated["Air Minum (L)"]),
                    str(updated["Durasi Tidur"]),
                    str(updated["Jam Tidur"]),
                    str(updated["Haid"]),
                    int(item_id),
                    st.session_state.user_id
                ))
        conn.commit()

    # Muat Ulang Data Baru dari Database agar Sinkron setelah Edit/Hapus
    c.execute(
        "SELECT id, tanggal, waktu, aktivitas, item, jumlah, mood, kalori, gula, air_minum, durasi_tidur, jam_tidur, haid FROM activity_history WHERE user_id = ?",
        (st.session_state.user_id,)
    )
    rows = c.fetchall()
    st.session_state.history = []
    for row in rows:
        try:
            durasi_tidur_val = float(row[10]) if row[10] not in (None, "-", "None") else 0.0
        except ValueError:
            durasi_tidur_val = 0.0

        db_date = row[1]
        try:
            formatted_date = datetime.datetime.strptime(db_date, "%Y-%m-%d").strftime("%d-%m-%Y")
        except:
            formatted_date = db_date

        st.session_state.history.append({
            "id": row[0],
            "tanggal": formatted_date,
            "Waktu": row[2],
            "Aktivitas": row[3],
            "Item": row[4],
            "Jumlah": row[5],
            "Mood": row[6],
            "Est. Kalori (Kal)": row[7],
            "Est. Gula (g)": row[8],
            "Air Minum (L)": row[9],
            "Durasi Tidur": durasi_tidur_val,
            "Jam Tidur": row[11],
            "Haid": row[12]
        })

    # Hapus state editor agar memaksa Streamlit merender ulang tabel menggunakan data baru
    if "history_editor" in st.session_state:
        del st.session_state.history_editor


def history_page():

    st.title("Catatan Aktivitas")
    st.write("---")

    # ==================== FORCE LOAD DARI DB BILA MEMORI RIWAYAT KOSONG ====================
    if not st.session_state.history:
        c.execute(
            "SELECT id, tanggal, waktu, aktivitas, item, jumlah, mood, kalori, gula, air_minum, durasi_tidur, jam_tidur, haid FROM activity_history WHERE user_id = ?",
            (st.session_state.user_id,)
        )
        rows = c.fetchall()
        for row in rows:
            try:
                durasi_tidur_val = float(row[10]) if row[10] not in (None, "-", "None") else 0.0
            except ValueError:
                durasi_tidur_val = 0.0

            db_date = row[1]
            try:
                formatted_date = datetime.datetime.strptime(db_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            except:
                formatted_date = db_date

            st.session_state.history.append({
                "id": row[0],
                "tanggal": formatted_date,
                "Waktu": row[2],
                "Aktivitas": row[3],
                "Item": row[4],
                "Jumlah": row[5],
                "Mood": row[6],
                "Est. Kalori (Kal)": row[7],
                "Est. Gula (g)": row[8],
                "Air Minum (L)": row[9],
                "Durasi Tidur": durasi_tidur_val,
                "Jam Tidur": row[11],
                "Haid": row[12]
            })

    # Jika setelah dicek ke database pun memang belum pernah menginput data sama sekali
    if not st.session_state.history:
        st.info("Belum ada riwayat")
        return

    # Membuat DataFrame dari data riwayat
    df_hist = pd.DataFrame(st.session_state.history)

    st.info("Klik dua kali pada kotak tabel untuk mengubah isi. Untuk menghapus baris, klik/centang bagian kiri baris lalu tekan **Delete** pada keyboard Anda atau klik **ikon tempat sampah** di kanan atas tabel.")

    # Render Tabel Interaktif menggunakan st.data_editor
    st.data_editor(
        df_hist,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "id": None,  # Sembunyikan ID agar lebih rapi bagi user
            "tanggal": st.column_config.TextColumn("Tanggal", help="Format: DD-MM-YYYY"),
            "Waktu": st.column_config.TextColumn("Waktu"),
            "Aktivitas": st.column_config.TextColumn("Aktivitas", disabled=True), 
            "Item": st.column_config.TextColumn("Item / Kegiatan"),
            "Jumlah": st.column_config.NumberColumn("Jumlah", min_value=0.0, step=0.1),
            "Mood": st.column_config.SelectboxColumn("Mood", options=["🤩 Bahagia", "😐 Standar", "🥲 Sedih", "😡 Stress"]),
            "Est. Kalori (Kal)": st.column_config.NumberColumn("Kalori (Kal)", step=1.0),
            "Est. Gula (g)": st.column_config.NumberColumn("Gula (g)", step=1.0),
            "Air Minum (L)": st.column_config.NumberColumn("Air Minum (L)", step=0.1),
            "Durasi Tidur": st.column_config.NumberColumn("Durasi Tidur (Jam)", step=0.5),
            "Jam Tidur": st.column_config.TextColumn("Jam Tidur"),
            "Haid": st.column_config.SelectboxColumn("Haid", options=["Tidak", "Ya (Sedang Menstruasi)"])
        },
        key="history_editor",
        on_change=on_table_change
    )
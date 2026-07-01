import streamlit as st

# CONFIG (Harus diletakkan paling atas sebagai perintah Streamlit pertama)
st.set_page_config(
    page_title="Sistem Manajemen Hormon & Kesehatan Wanita",
    layout="wide"
)

from streamlit_option_menu import option_menu

from auth import auth_page

from dashboard import dashboard_page
from profile import profile_page
from input_activity import input_activity_page
from history import history_page
from summary import summary_page
from prediction import prediction_page

# SESSION
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"
    
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "history" not in st.session_state:
    st.session_state.history = []

if "selected_mood" not in st.session_state:
    st.session_state.selected_mood = "🤔"

# AUTH
if not st.session_state.logged_in:

    auth_page()
    st.stop()

# LOAD HISTORY FROM DATABASE ON LOGIN
if st.session_state.logged_in and not st.session_state.get("history_loaded", False):
    from database import c
    import datetime
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
            
        # Format date from YYYY-MM-DD to DD-MM-YYYY
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
    st.session_state.history_loaded = True

  
# SIDEBAR
  
with st.sidebar:

    st.title("Sistem Kesehatan Wanita")

    from database import c
    c.execute(
    "SELECT nama FROM profile WHERE user_id=?",
    (st.session_state.user_id,)
    )

    nama_user = c.fetchone()


    selected = option_menu(
        menu_title="Menu",

        options=[
            "Beranda",
            "Data Diri",
            "Aktivitas",
            "Catatan Aktivitas",
            "Ringkasan Aktivitas",
            "Prediksi Kesehatan PCOS"
        ],

        icons=[
            "house",
            "person",
            "pencil-square",
            "clock-history",
            "bar-chart",
            "robot"
        ],

        default_index=0
    )

    st.write("---")

    st.html(
        """
        <style>
        /* Target universal untuk tombol logout di sidebar */
        [data-testid="stSidebar"] button {
            background-color: #ffffff !important;
            color: #2E2E2E !important;
            border: 1px solid #d3d3d3 !important;
            transition: all 0.3s ease;
        }
        [data-testid="stSidebar"] button:hover {
            background-color: #f8f9fa !important;
            color: #ff4b4b !important;
            border-color: #ff4b4b !important;
        }
        /* Bypass text inside button container */
        [data-testid="stSidebar"] button p {
            color: inherit !important;
        }
        </style>
        """
    )

    if st.button(
        "Keluar",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.history = []
        if "history_loaded" in st.session_state:
            del st.session_state.history_loaded
        st.rerun()

  
# ROUTING
  
if selected == "Beranda":
    dashboard_page()

elif selected == "Data Diri":
    profile_page()

elif selected == "Aktivitas":
    input_activity_page()

elif selected == "Catatan Aktivitas":
    history_page()

elif selected == "Ringkasan Aktivitas":
    summary_page()

elif selected == "Prediksi Kesehatan PCOS":
    prediction_page()
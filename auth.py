import streamlit as st
import base64
import re 

from database import conn, c


 
# SESSION STATE INITIALIZATION
 
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"


 
# CSS
 
def add_bg():
    try:
        with open("desainbg.png", "rb") as img:
            encoded = base64.b64encode(img.read()).decode()
    except FileNotFoundError:
        # Fallback ketika gambar tidak ditemukan
        encoded = ""

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        header {{ visibility: hidden; }}
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        /* CONTAINER UTAMA  */
        div[data-testid="stColumn"]:nth-of-type(2) > div[data-testid="stVerticalBlock"] {{
            background: rgba(255, 255, 255, 0.18);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            padding: 45px;
            border-radius: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-top: 60px;
        }}

        /* TITLE */
        .title {{
            text-align: center !important;
            font-size: 55px !important; 
            font-weight: bold !important;
            color: white !important;
            letter-spacing: 2px !important;
            margin-bottom: 25px !important;
            -webkit-text-stroke: 1.0px black;
            text-shadow: 0 4px 15px rgba(0,0,0,0.35);
        }}

        /* SUBTEXT */
        .subtext {{
            text-align: center;
            color: black;
            margin-top: 20px;
            margin-bottom: 10px;
            font-size: 16px;
            font-weight: 600;
        }}

        /* TEXT INPUT LABELS (Username & Password) */
        .stTextInput label p {{
            font-size: 20px !important; 
            color: #000000 !important;     
        }}

        /* INPUT FIELD */
        .stTextInput > div > div > input {{
            border-radius: 15px;
            height: 48px;
            background-color: rgba(255, 255, 255, 0.7);
            color: black;
        }}

        /* BUTTON */
        .stButton > button {{
            border-radius: 15px;
            height: 48px;
            font-size: 26px !important; 
            font-weight: bold !important;   
            border: none;
            background-color: #FFC0CB;
            color: black;
            transition: 0.3s;
            margin-top: 10px;
        }}

        .stButton > button:hover {{
            background-color: #ff9eb5;
            color: black;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


 
# LOGIN PAGE VIEW
 
def login_page():
    add_bg()

    col1, col2, col3 = st.columns([0.5, 1.4, 0.5]) 

    with col2:
        st.html("<div></div>")

        st.markdown("<p class='title'>Sistem Kesehatan Wanita</p>", unsafe_allow_html=True)

        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        st.write("")

        if st.button("Login", use_container_width=True):
            if username == "" or password == "":
                st.warning("Semua field harus diisi")
            else:
                c.execute(
                    "SELECT * FROM users WHERE username=? AND password=?", 
                    (username, password)
                )
                user = c.fetchone()

                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_id = user[0]
                    st.success("Login berhasil")
                    st.rerun()
                else:
                    st.error("Username atau password salah")

        st.markdown("<p class='subtext'>Belum punya akun?</p>", unsafe_allow_html=True)

        if st.button("Sign Up", use_container_width=True):
            st.session_state.auth_page = "signup"
            st.rerun()


 
# SIGNUP PAGE VIEW
def signup_page():
    add_bg()

    col1, col2, col3 = st.columns([0.5, 1.4, 0.5])

    with col2:
        st.html("<div></div>")

        st.markdown("<p class='title'>Sistem Kesehatan Wanita</p>", unsafe_allow_html=True)

        username = st.text_input("Username", key="signup_user")
        password = st.text_input("Password", type="password", key="signup_pass")

        st.write("")

        if st.button("Create Account", use_container_width=True):
            if username == "" or password == "":
                st.warning("Semua field harus diisi")
            
            # 1. Validasi minimal 6 karakter untuk Username
            elif len(username) < 6:
                st.error("Username harus minimal 6 karakter!")
            
            # 2. Validasi minimal 6 karakter untuk Password
            elif len(password) < 6:
                st.error("Password harus minimal 6 karakter!")
            
            # 3. Validasi kombinasi Password (harus ada huruf, angka, dan simbol)
            elif not (re.search(r"[A-Za-z]", password) and 
                      re.search(r"[0-9]", password) and 
                      re.search(r"[!@#$%^&*(),.?\":{}|<>_+-=~`[\]\\/;']", password)):
                st.error("Password harus mengandung kombinasi huruf, angka, dan simbol!")
                
            else:
                c.execute("SELECT * FROM users WHERE username=?", (username,))
                existing = c.fetchone()

                if existing:
                    st.warning("Username sudah digunakan")
                else:
                    c.execute(
                        "INSERT INTO users (username, password) VALUES (?, ?)", 
                        (username, password)
                    )
                    conn.commit()
                    st.success("Akun berhasil dibuat!")
                    st.session_state.auth_page = "login"
                    st.rerun()

        st.markdown("<p class='subtext'>Sudah punya akun?</p>", unsafe_allow_html=True)

        if st.button("Back to Login", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()


 
# ROUTER
def auth_page():
    if st.session_state.auth_page == "login":
        login_page()
    else:
        signup_page()

# Menjalankan aplikasi
if __name__ == "__main__":
    st.set_page_config(page_title="Login & Signup", layout="centered")
    auth_page()
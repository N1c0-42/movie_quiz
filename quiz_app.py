import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import socket
import json
import os
import time
import streamlit.components.v1 as components

# --- KONFIGURATION ---
DB_FILE = "quiz_data.json"
HTML_FILE = "movie_quiz_board.htm"

# --- MODERNES DESIGN (CSS) ---
MODERN_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');

    .stApp {
        background: radial-gradient(circle at top, #0f172a, #020617);
        color: #f8fafc;
        font-family: 'Poppins', sans-serif;
    }
    
    .answer-card {
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 20px;
        padding: 24px;
        border-left: 6px solid #f5c518;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        animation: fadeIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    @keyframes fadeIn { 
        from { opacity: 0; transform: translateY(15px); } 
        to { opacity: 1; transform: translateY(0); } 
    }
    
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #f5c518, #eab308);
        color: #020617 !important;
        font-weight: 800 !important;
        font-size: 1.3rem !important; /* Größere Schrift für Tablets */
        letter-spacing: 0.5px;
        border-radius: 16px !important; /* Etwas runder */
        border: none !important;
        height: 4.5rem; /* Höherer Button für leichteres Tippen */
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(245, 197, 24, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(245, 197, 24, 0.4);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }

    .name-badge {
        background: rgba(245, 197, 24, 0.1);
        border: 1px solid rgba(245, 197, 24, 0.3);
        color: #f5c518;
        padding: 10px 20px;
        border-radius: 24px;
        font-weight: 600;
        font-size: 1.1rem;
        display: inline-block;
        margin-bottom: 25px;
        box-shadow: 0 0 15px rgba(245, 197, 24, 0.1);
    }
    
    /* Inputs - Tablet Optimized */
    .stTextArea textarea {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 2px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        color: white !important;
        font-family: 'Poppins', sans-serif !important;
        font-size: 1.2rem !important; /* Bessere Lesbarkeit */
        padding: 16px !important; /* Mehr Platz zum Tippen */
        line-height: 1.5 !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #f5c518 !important;
        box-shadow: 0 0 0 2px rgba(245, 197, 24, 0.3) !important;
    }
    
    .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 2px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        font-size: 1.2rem !important;
        padding: 4px !important;
    }

    /* Verstecke Standard Streamlit Elemente für sauberen Look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
</style>
"""

def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

st.set_page_config(page_title="Filmquiz Deluxe", page_icon="🎬", layout="wide")
st.markdown(MODERN_STYLE, unsafe_allow_html=True)

query_params = st.query_params
is_player = query_params.get("view") == "player"

# --- AUTO-REFRESH LOGIK FÜR DEN MODERATOR ---
@st.fragment(run_every=3) # Aktualisiert diesen Teil alle 3 Sekunden automatisch
def show_answers_live():
    data = load_data()
    if data:
        st.subheader(f"Eingegangene Lösungen ({len(data)}):")
        for user, ans in data.items():
            st.markdown(f"""
                <div class="answer-card">
                    <small style="color: #f5c518; font-weight: 600; letter-spacing: 0.5px;">{user.upper()}</small><br>
                    <p style="margin-top:8px; font-size: 1.1rem; color: #f8fafc;">{ans}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Warten auf die Teilnehmer... (Aktualisiert automatisch)")

if is_player:
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    if "player_name" not in st.session_state:
        st.session_state.player_name = None
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    if st.session_state.player_name is None:
        st.title("Willkommen beim Quiz! 🍿")
        with st.form("name_form"):
            input_name = st.selectbox("Wähle deinen Namen:", ["Daniel", "Marlon", "Sabbl", "Nico", "Gast"])
            if st.form_submit_button("Los geht's! 🚀"):
                st.session_state.player_name = input_name
                st.rerun()
    
    elif st.session_state.submitted:
        st.title("Abgeschickt!")
        st.markdown(f'<div class="name-badge">{st.session_state.player_name}</div>', unsafe_allow_html=True)
        st.write("Deine Antwort ist beim Moderator. Warte auf die nächste Runde.")
        if st.button("Nächste Frage beantworten"):
            st.session_state.submitted = False
            st.rerun()

    else:
        st.title("Deine Antwort 📱")
        st.markdown(f'<div class="name-badge">{st.session_state.player_name}</div>', unsafe_allow_html=True)
        with st.form("quiz_form"):
            answer = st.text_area("Lösung:", placeholder="Tippe hier...", height=120)
            if st.form_submit_button("Antwort abschicken 🚀"):
                if answer:
                    data = load_data()
                    data[st.session_state.player_name] = answer
                    save_data(data)
                    st.session_state.submitted = True
                    st.rerun()
else:
    # --- MODERATOR & SCOREBOARD ---
    st.sidebar.title("🎬 Regie")
    role = st.sidebar.radio("Ansicht:", ["Moderator (Tablet)", "Scoreboard (Beamer)"])

    if role == "Moderator (Tablet)":
        st.title("Moderator Zentrale 🎤")
        
        local_ip = get_local_ip()
        player_url = f"http://{local_ip}:8501/?view=player"
        
        col1, col2 = st.columns([1, 2])
        with col1:
            qr = qrcode.make(player_url)
            buf = BytesIO()
            qr.save(buf)
            st.image(buf.getvalue(), caption="Scan für Teilnehmer", width=150)
        with col2:
            st.write(f"Link: `{player_url}`")
            if st.button("🗑️ Liste für neue Runde leeren"):
                save_data({})
                st.rerun()

        st.divider()
        # HIER WIRD DIE LIVE-FUNKTION AUFGERUFEN
        show_answers_live()

    elif role == "Scoreboard (Beamer)":
        if os.path.exists(HTML_FILE):
            with open(HTML_FILE, "r", encoding="utf-8") as f:
                html_content = f.read()
            components.html(html_content, height=1200)
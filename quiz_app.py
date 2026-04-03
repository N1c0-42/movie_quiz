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

    /* Styling für die Tabs (Moderator Navigation) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(30, 41, 59, 0.5);
        padding: 8px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stTabs [data-baseweb="tab"] {
        height: 60px;
        background-color: transparent !important;
        border-radius: 12px !important;
        border: none !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
        padding: 0 30px !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #f5c518 !important;
        color: #020617 !important;
        box-shadow: 0 4px 15px rgba(245, 197, 24, 0.3);
    }

    /* Verstecke Standard Streamlit Elemente für sauberen Look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background: transparent !important;}
</style>
"""

ALL_PLAYERS = ["Daniel", "Marlon", "Sabbl", "Nico"]

def load_data():
    # Struktur: scores[Name] = {"pts": 0, "qs": 0}
    default = {
        "answers": {}, 
        "last_clear": 0, 
        "scores": {name: {"pts": 0, "qs": 0} for name in ALL_PLAYERS}, 
        "points_given": []
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                # Migration zu Objekt-Struktur falls nötig
                if "scores" in data:
                    for name in ALL_PLAYERS:
                        if name in data["scores"] and isinstance(data["scores"][name], int):
                            data["scores"][name] = {"pts": data["scores"][name], "qs": 0}
                else:
                    data["scores"] = default["scores"]
                
                if "points_given" not in data: data["points_given"] = []
                return data
        except: return default
    return default

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

def reset_data():
    data = load_data()
    
    # Automatische Moderator-Erkennung:
    # Wer aus ALL_PLAYERS hat KEINE Antwort in data["answers"]?
    submitted_names = list(data["answers"].keys())
    missing_players = [p for p in ALL_PLAYERS if p not in submitted_names]
    
    # Wenn genau einer fehlt, war das wohl der Moderator
    if len(missing_players) == 1:
        mod_name = missing_players[0]
        data["scores"][mod_name]["qs"] += 1
    
    data["answers"] = {}
    data["points_given"] = []
    data["last_clear"] = time.time()
    save_data(data)

def hard_reset_quiz():
    default = {
        "answers": {}, 
        "last_clear": time.time(), 
        "scores": {name: {"pts": 0, "qs": 0} for name in ALL_PLAYERS}, 
        "points_given": []
    }
    save_data(default)

def update_score(name, delta):
    data = load_data()
    if name in data["scores"]:
        data["scores"][name]["pts"] += delta
        if delta > 0:
            data["points_given"].append(name)
    save_data(data)

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
    answers = data.get("answers", {})
    points_given = data.get("points_given", [])
    
    if answers:
        st.subheader(f"Eingegangene Lösungen ({len(answers)}):")
        for user, ans in answers.items():
            col_ans, col_score = st.columns([4, 1])
            with col_ans:
                st.markdown(f"""
                    <div class="answer-card">
                        <small style="color: #f5c518; font-weight: 600; letter-spacing: 0.5px;">{user.upper()}</small><br>
                        <p style="margin-top:8px; font-size: 1.1rem; color: #f8fafc;">{ans}</p>
                    </div>
                """, unsafe_allow_html=True)
            with col_score:
                # Button sperren, wenn schon ein Punkt vergeben wurde
                is_disabled = user in points_given
                button_label = "✅ +1" if is_disabled else "🎯 +1"
                
                if st.button(button_label, key=f"score_{user}", disabled=is_disabled, use_container_width=True):
                    update_score(user, 1)
                    st.toast(f"Punkt für {user}!")
                    time.sleep(0.5) # Kurze Pause für den Toast
                    st.rerun() # Ganze Seite neu laden, um Scoreboard-Tab zu aktualisieren
    else:
        st.info("Warten auf die Teilnehmer... (Aktualisiert automatisch)")

if is_player:
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    # Session State Initialisierung
    if "player_name" not in st.session_state:
        st.session_state.player_name = None
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "last_sync" not in st.session_state:
        st.session_state.last_sync = 0

    # Daten laden für Sync und Status
    data = load_data()
    global_last_clear = data.get("last_clear", 0)

    # Automatischer Reset, wenn der Moderator die Liste geleert hat
    if global_last_clear > st.session_state.last_sync:
        st.session_state.submitted = False
        st.session_state.last_sync = global_last_clear
        if "last_answer" in st.session_state:
            del st.session_state.last_answer
        st.rerun()

    if st.session_state.player_name is None:
        st.title("Willkommen beim Quiz! 🍿")
        with st.form("name_form"):
            input_name = st.selectbox("Wähle deinen Namen:", ["Daniel", "Marlon", "Sabbl", "Nico"])
            if st.form_submit_button("Los geht's! 🚀"):
                st.session_state.player_name = input_name
                st.rerun()
    
    elif st.session_state.submitted:
        st.title("Abgeschickt!")
        st.markdown(f'<div class="name-badge">{st.session_state.player_name}</div>', unsafe_allow_html=True)
        
        # Eigene Antwort anzeigen
        if "last_answer" in st.session_state:
            st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; border-left: 4px solid #f5c518; margin-bottom: 20px;">
                    <small style="opacity: 0.6;">Deine Antwort:</small><br>
                    <div style="font-size: 1.1rem; margin-top: 5px;">{st.session_state.last_answer}</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.success("Deine Antwort ist beim Moderator.")
        
    # LIVE STATUS FRAGMENT
        @st.fragment(run_every=3)
        def show_player_status():
            current_data = load_data()
            current_answers = current_data.get("answers", {})
            num_ready = len(current_answers)
            
            # Wer hat schon abgegeben?
            ready_names = ", ".join([f"✅ {name}" for name in current_answers.keys()])
            if not ready_names: ready_names = "Noch niemand..."

            st.markdown(f"""
                <div style="text-align:center; padding: 20px; border: 1px dashed #f5c518; border-radius: 15px; background: rgba(245, 197, 24, 0.05); margin-bottom: 20px;">
                    <span style="font-size: 1.5rem; font-weight: 600;">{num_ready} / 3</span><br>
                    <div style="margin: 10px 0; font-size: 0.9rem; color: #94a3b8;">{ready_names}</div>
                    <small style="opacity: 0.7;">Warte auf die nächste Runde (automatisch)...</small>
                </div>
            """, unsafe_allow_html=True)
            
            # Check for Reset inside Fragment to force UI switch
            global_last_clear_inner = current_data.get("last_clear", 0)
            if global_last_clear_inner > st.session_state.last_sync:
                st.rerun()
        
        show_player_status()
        
        if st.button("✏️ Lösung korrigieren"):
            st.session_state.submitted = False
            st.rerun()

    else:
        st.title("Deine Antwort 📱")
        st.markdown(f'<div class="name-badge">{st.session_state.player_name}</div>', unsafe_allow_html=True)
        
        # Vorherige Antwort laden, falls vorhanden (für Korrekturen)
        prev_val = st.session_state.get("last_answer", "")
        
        with st.form("quiz_form"):
            answer = st.text_area("Lösung:", value=prev_val, placeholder="Tippe hier...", height=120)
            if st.form_submit_button("Antwort abschicken 🚀"):
                if answer:
                    data = load_data()
                    data["answers"][st.session_state.player_name] = answer
                    save_data(data)
                    st.session_state.last_answer = answer
                    st.session_state.submitted = True
                    st.rerun()
else:
    # --- MODERATOR & SCOREBOARD ---
    tab_regie, tab_score = st.tabs(["🎤 MODERATOR", "🏆 SCOREBOARD"])

    with tab_regie:
        st.title("Moderator Zentrale 🎤")
        
        # Dynamische URL Erkennung (lokal vs cloud)
        if "localhost" in st.query_params or "127.0.0.1" in st.query_params:
             player_url = f"http://{get_local_ip()}:8501/?view=player"
        else:
             player_url = "https://moviequizgit-mwatvzmqtcp3aq7hryuvxc.streamlit.app/?view=player"
        
        col1, col2 = st.columns([1, 2])
        with col1:
            qr = qrcode.make(player_url)
            buf = BytesIO()
            qr.save(buf)
            st.image(buf.getvalue(), caption="Scan für Teilnehmer", width=200)
        with col2:
            st.write(f"Direktlink: `{player_url}`")
            if st.button("🗑️ Liste für neue Runde leeren", use_container_width=True, type="primary"):
                reset_data()
                st.rerun()
            
            # --- GLOBALER RESET ---
            with st.expander("⚠️ Gefahrenzone"):
                if st.button("🔥 GESAMTES QUIZ ZURÜCKSETZEN", use_container_width=True):
                    hard_reset_quiz()
                    st.success("Alle Daten wurden gelöscht!")
                    time.sleep(1)
                    st.rerun()

        st.divider()
        show_answers_live()

    with tab_score:
        if os.path.exists(HTML_FILE):
            data = load_data()
            scores_json = json.dumps(data.get("scores", {}))
            with open(HTML_FILE, "r", encoding="utf-8") as f:
                html_content = f.read()

            # Injiziere die Scores als globale JS Variable vor dem schließenden </head>
            sync_script = f"<script>window.pythonScores = {scores_json};</script>"
            html_content = html_content.replace("</head>", f"{sync_script}</head>")

            components.html(html_content, height=1200)
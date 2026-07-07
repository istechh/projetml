import streamlit as st
import requests
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "https://projetchurn.onrender.com").rstrip("/")
XOF_PER_USD = 600

st.set_page_config(
    page_title="Churn Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# ICONES SVG monochromes (un seul ton par contexte -> look sobre et pro)
# ---------------------------------------------------------------------------
ICONS = {
    "logo": """<svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>
        <path d="M12 21C9.5 21 7.2 19.9 5.6 18.1" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-dasharray="1 4" opacity="0.6"/>
        <path d="M12 7V12L15 15" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>""",
    "users": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M16 11C17.6569 11 19 9.65685 19 8C19 6.34315 17.6569 5 16 5" stroke="#475569" stroke-width="1.7" stroke-linecap="round"/><path d="M2 19C2 15.6863 5.13401 13 9 13C12.866 13 16 15.6863 16 19" stroke="#475569" stroke-width="1.7" stroke-linecap="round"/><path d="M18 13.5C20.3 14.1 22 16.2 22 18.7" stroke="#475569" stroke-width="1.7" stroke-linecap="round"/><circle cx="9" cy="7" r="4" stroke="#475569" stroke-width="1.7"/></svg>""",
    "alert": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M12 9V13" stroke="#b91c1c" stroke-width="2" stroke-linecap="round"/><circle cx="12" cy="16.3" r="0.9" fill="#b91c1c"/><path d="M10.6 4.7C11.2 3.6 12.8 3.6 13.4 4.7L20.5 17.5C21.1 18.6 20.3 20 19 20H5C3.7 20 2.9 18.6 3.5 17.5L10.6 4.7Z" stroke="#b91c1c" stroke-width="1.6" stroke-linejoin="round"/></svg>""",
    "check": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="#15803d" stroke-width="1.6"/><path d="M8 12.5L10.7 15L16 9" stroke="#15803d" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "chart": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M4 20V10" stroke="#475569" stroke-width="1.7" stroke-linecap="round"/><path d="M10 20V4" stroke="#475569" stroke-width="1.7" stroke-linecap="round"/><path d="M16 20V13" stroke="#475569" stroke-width="1.7" stroke-linecap="round"/><path d="M2 20H22" stroke="#475569" stroke-width="1.7" stroke-linecap="round"/></svg>""",
    "trend": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M3 17L9 11L13 15L21 7" stroke="#475569" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/><path d="M15 7H21V13" stroke="#475569" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
    "list": """<svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M8 6H21" stroke="#475569" stroke-width="1.7" stroke-linecap="round"/><path d="M8 12H21" stroke="#475569" stroke-width="1.7" stroke-linecap="round"/><path d="M8 18H21" stroke="#475569" stroke-width="1.7" stroke-linecap="round"/><path d="M3 6H3.01" stroke="#475569" stroke-width="2.2" stroke-linecap="round"/><path d="M3 12H3.01" stroke="#475569" stroke-width="2.2" stroke-linecap="round"/><path d="M3 18H3.01" stroke="#475569" stroke-width="2.2" stroke-linecap="round"/></svg>""",
}

def icon(name: str) -> str:
    return ICONS.get(name, "")

# ---------------------------------------------------------------------------
# STYLE — palette sobre : 1 couleur de marque (navy) + gris neutres + rouge/vert
# réservés uniquement au statut de risque.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    --navy: #1c3d5a;
    --navy-dark: #142c40;
    --ink: #1f2937;
    --muted: #64748b;
    --border: #e5e7eb;
    --bg: #f8fafc;
    --danger: #dc2626;
    --danger-bg: #fef2f2;
    --success: #16a34a;
    --success-bg: #f0fdf4;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--ink); }
.main { background: var(--bg); }
.main > .block-container { padding: 1.5rem 2rem 2.5rem 2rem; max-width: 1180px; }

/* ---------- Sidebar : couleur unique, plate ---------- */
[data-testid="stSidebar"] { background: var(--navy); }
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.92); }

.sidebar-brand {
    display: flex; align-items: center; gap: 10px;
    padding: 4px 0 18px 6px; border-bottom: 1px solid rgba(255,255,255,0.12);
    margin-bottom: 16px;
}
.sidebar-brand h2 { color: #fff; font-size: 1.05rem; margin: 0; font-weight: 700; }
.sidebar-brand p { color: rgba(255,255,255,0.55); font-size: 0.75rem; margin: 0; }

[data-testid="stSidebar"] .stButton > button {
    background: transparent !important; border: none !important;
    color: rgba(255,255,255,0.75) !important; text-align: left !important;
    justify-content: flex-start !important;
    padding: 9px 12px !important; border-radius: 8px !important;
    font-weight: 500 !important; width: 100% !important;
    transition: background 0.15s ease, color 0.15s ease;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #fff !important;
}
div[data-testid="stSidebarNav"] { display: none; }

.sidebar-footer {
    margin-top: 24px; padding-top: 14px; border-top: 1px solid rgba(255,255,255,0.12);
    font-size: 0.72rem; color: rgba(255,255,255,0.4);
}

/* ---------- Cartes / KPI : plates, une seule ombre légère ---------- */
.kpi-card {
    background: #fff; padding: 16px 18px; border-radius: 10px;
    border: 1px solid var(--border);
    height: 100%;
}
.kpi-label {
    font-size: 0.78rem; color: var(--muted); font-weight: 500;
    display: flex; align-items: center; gap: 6px;
}
.kpi-value { font-size: 1.55rem; font-weight: 700; color: var(--ink); margin: 6px 0 0 0; line-height: 1.2; }
.kpi-sub { font-size: 0.76rem; color: #94a3b8; margin-top: 2px; }

.section-header {
    font-size: 1rem; font-weight: 600; color: var(--ink);
    margin: 26px 0 12px 0; display: flex; align-items: center; gap: 8px;
}

/* ---------- Formulaires ---------- */
.stForm {
    background: #fff; padding: 22px; border-radius: 12px;
    border: 1px solid var(--border);
}
.stForm h3, .stForm strong { color: var(--ink); }

/* ---------- Résultat de prédiction ---------- */
.result-card {
    padding: 18px 20px; border-radius: 10px; margin-top: 14px;
    border: 1px solid var(--border); border-left: 4px solid;
    display: flex; align-items: center; gap: 14px;
}
.result-card.risk { background: var(--danger-bg); border-left-color: var(--danger); }
.result-card.stable { background: var(--success-bg); border-left-color: var(--success); }
.result-card h3 { font-size: 1.05rem; margin: 0; }
.result-card p { font-size: 0.88rem; }

/* ---------- Tabs (mobile-friendly) ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 0; }
.stTabs [data-baseweb="tab"] {
    font-size: 0.85rem; font-weight: 500; padding: 8px 14px;
}
.stTabs [aria-selected="true"] { font-weight: 600; }

/* ---------- Badge API ---------- */
.api-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #fff; padding: 6px 14px; border-radius: 8px;
    font-size: 0.78rem; color: var(--muted); border: 1px solid var(--border);
}
.dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }
.dot.green { background: var(--success); }
.dot.red { background: var(--danger); }

/* ---------- Boutons génériques (hors sidebar) ---------- */
.stFormSubmitButton > button {
    border-radius: 8px !important;
    background: var(--navy) !important;
    color: #fff !important; border: none !important;
    font-weight: 600 !important;
    transition: background 0.15s ease !important;
    box-shadow: none !important;
}
.stFormSubmitButton > button:hover { background: var(--navy-dark) !important; }

.stDownloadButton > button {
    border-radius: 8px !important; border: 1px solid var(--border) !important;
    background: #fff !important; color: var(--ink) !important; font-weight: 500 !important;
}
.stDownloadButton > button:hover { background: var(--bg) !important; border-color: var(--navy) !important; }

/* ---------------------------------------------------------------------
   RESPONSIVE MOBILE
   --------------------------------------------------------------------- */
@media (max-width: 768px) {
    .main > .block-container { padding: 0.6rem 0.6rem 2rem 0.6rem; max-width: 100%; }

    h1, h2 { font-size: 1.05rem !important; }
    .section-header { font-size: 0.82rem; margin: 12px 0 8px 0; }
    .section-header svg { display: none; }

    .sidebar-brand { padding: 2px 0 12px 4px; margin-bottom: 10px; }
    .sidebar-brand h2 { font-size: 0.85rem; }
    .sidebar-brand p { font-size: 0.65rem; }
    .sidebar-footer { font-size: 0.6rem; margin-top: 12px; padding-top: 8px; }
    [data-testid="stSidebar"] .stButton > button { padding: 6px 10px !important; font-size: 0.8rem !important; }

    .kpi-card { padding: 10px 12px; margin-bottom: 6px; }
    .kpi-value { font-size: 1.1rem; margin-top: 2px; }
    .kpi-label { font-size: 0.7rem; }
    .kpi-label svg { width: 13px; height: 13px; }
    .kpi-sub { font-size: 0.65rem; }

    .stForm { padding: 10px; }
    .stForm strong { font-size: 0.82rem; }
    .stForm .stSelectbox label, .stForm .stSlider label, .stForm .stNumberInput label {
        font-size: 0.78rem !important;
    }

    .stTabs [data-baseweb="tab"] { font-size: 0.75rem; padding: 6px 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; overflow-x: auto; }

    .result-card { flex-direction: row; align-items: center; gap: 10px; padding: 10px 12px; margin-top: 10px; }
    .result-card h3 { font-size: 0.85rem; }
    .result-card p { font-size: 0.76rem; margin: 2px 0 0 0 !important; }
    .result-card svg { width: 20px; height: 20px; flex-shrink: 0; }

    .stDataFrame { font-size: 0.72rem !important; }
    .stDataFrame td, .stDataFrame th { padding: 4px 6px !important; }

    .stAlert { font-size: 0.78rem !important; padding: 8px 12px !important; }
    .stAlert svg { width: 16px !important; height: 16px !important; }

    .stDownloadButton > button { font-size: 0.78rem !important; padding: 6px 12px !important; }

    .api-badge { font-size: 0.65rem; padding: 4px 8px; }

    .js-plotly-plot { max-height: 180px !important; }
    .js-plotly-plot .plotly .gtitle { font-size: 11px !important; }
    .js-plotly-plot .plotly .numbershow { font-size: 11px !important; }

    .st-emotion-cache-1bv6p78, .st-emotion-cache-18ni7ap { gap: 0.4rem; }
}

@media (max-width: 480px) {
    .main > .block-container { padding: 0.4rem 0.4rem 1.5rem 0.4rem; }

    .kpi-card { padding: 8px 10px; }
    .kpi-value { font-size: 0.95rem; }
    .kpi-label { font-size: 0.65rem; }
    .kpi-sub { font-size: 0.6rem; }

    .stForm { padding: 8px; }

    .js-plotly-plot { max-height: 150px !important; }
}
</style>
""", unsafe_allow_html=True)

# --- Session state ---
def load_history():
    try:
        r = requests.get(f"{API_URL}/history", timeout=5)
        if r.status_code == 200:
            data = r.json().get("history", [])
            st.session_state.history = data
            st.session_state.history_df = pd.DataFrame(data)
            return
    except Exception:
        pass
    st.session_state.history = []
    st.session_state.history_df = pd.DataFrame()

load_history()

# --- API check ---
api_ok = False
api_info = None
try:
    r = requests.get(f"{API_URL}/", timeout=5)
    if r.status_code == 200:
        api_info = r.json()
        api_ok = True
except Exception:
    pass

# --- Sidebar (branding only) ---
with st.sidebar:
    st.markdown(
        f'<div class="sidebar-brand">{ICONS["logo"]}<div><h2>Churn Intelligence</h2>'
        f'<p>Analyse prédictive client</p></div></div>',
        unsafe_allow_html=True,
    )
    if api_ok and api_info:
        st.markdown(
            f'<div style="padding:0 0 16px 6px;font-size:0.78rem;color:rgba(255,255,255,0.6);">'
            f'<span class="dot green"></span> API connectée &nbsp;·&nbsp; {api_info.get("model_type","")}'
            f'</div>', unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="padding:0 0 16px 6px;font-size:0.78rem;color:rgba(255,255,255,0.6);">'
            f'<span class="dot red"></span> API hors ligne'
            f'</div>', unsafe_allow_html=True,
        )
    st.markdown('<div class="sidebar-footer">v2.0 · Sénégal</div>', unsafe_allow_html=True)

# --- Tabs (mobile-friendly navigation) ---
tab_dash, tab_predict, tab_analyses = st.tabs(["📊 Dashboard", "🔍 Prédiction", "📈 Analyses"])

# ==============================
# TAB: DASHBOARD
# ==============================
with tab_dash:
    c1, c2 = st.columns(2)
    risky = sum(1 for h in st.session_state.history if h.get("churn_prediction") == 1)
    stable = sum(1 for h in st.session_state.history if h.get("churn_prediction") == 0)
    avg_risk = 0
    if st.session_state.history:
        avg_risk = sum(h.get("risk_score", 0) or h.get("churn_probability", 0) * 100 for h in st.session_state.history) / len(st.session_state.history)

    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{icon("users")} Total clients</div>'
                    f'<div class="kpi-value">{len(st.session_state.history) or "—"}</div>'
                    f'<div class="kpi-sub">analysés ce mois</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{icon("check")} Clients stables</div>'
                    f'<div class="kpi-value" style="color:var(--success);">{stable or "—"}</div>'
                    f'<div class="kpi-sub">{f"{stable/len(st.session_state.history)*100:.0f}%" if st.session_state.history else ""}</div></div>', unsafe_allow_html=True)
    with c2:
        pct = f"{risky/len(st.session_state.history)*100:.0f}%" if st.session_state.history else ""
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{icon("alert")} Risque élevé</div>'
                    f'<div class="kpi-value" style="color:var(--danger);">{risky or "—"}</div>'
                    f'<div class="kpi-sub">{pct}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{icon("chart")} Risque moyen</div>'
                    f'<div class="kpi-value">{f"{avg_risk:.1f}%" if st.session_state.history else "—"}</div>'
                    f'<div class="kpi-sub">sur tous les clients</div></div>', unsafe_allow_html=True)

    if st.session_state.history:
        st.markdown(f'<div class="section-header">{icon("trend")} Dernières analyses</div>', unsafe_allow_html=True)
        df_show = st.session_state.history_df.tail(5)[["date", "contract", "tenure", "monthly", "risk_score", "statut"]].copy()
        df_show.columns = ["Date", "Contrat", "Ancienneté", "Mensuel", "Risque", "Statut"]
        df_show["Mensuel"] = df_show["Mensuel"].apply(lambda x: f"{x:,.0f} F CFA")
        df_show["Risque"] = df_show["Risque"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_show, use_container_width=True, hide_index=True,
                     column_config={"Statut": st.column_config.Column(width="small")})
    else:
        st.info("💡 Aucune analyse pour l'instant. Va dans l'onglet **Prédiction** pour évaluer un client.")

    if api_info:
        st.markdown(f'<div style="margin-top:20px;font-size:0.8rem;color:var(--muted);">'
                    f'Modèle : {api_info.get("model_type")} · '
                    f'ROC-AUC : {api_info.get("model_roc_auc")} · '
                    f'Version API : {api_info.get("version")}</div>', unsafe_allow_html=True)

# ==============================
# TAB: PRÉDICTION
# ==============================
with tab_predict:
    if not api_ok:
        st.error(f"⚠️ Impossible de contacter l'API sur {API_URL}. Vérifiez que l'API est lancée.")
        st.stop()

    with st.form("churn_form"):
        st.markdown("**👤 Profil & Contrat**")
        c_prof = st.columns(2)
        with c_prof[0]:
            gender = st.selectbox("Sexe", ["Homme", "Femme"])
            SeniorCitizen = st.selectbox("Âge", [0, 1],
                                         format_func=lambda x: "Moins de 65 ans" if x == 0 else "65 ans ou plus")
            Partner = st.selectbox("En couple ?", ["Oui", "Non"])
        with c_prof[1]:
            Dependents = st.selectbox("Personnes à charge ?", ["Oui", "Non"])
            Contract = st.selectbox("Contrat", ["Mensuel (sans engagement)", "Engagement 1 an", "Engagement 2 ans"])
            tenure = st.slider("Ancienneté (mois)", 0, 100, 12)

        st.markdown("**💳 Facturation**")
        c_bill = st.columns(2)
        with c_bill[0]:
            PaperlessBilling = st.selectbox("Facture dématérialisée ?", ["Oui", "Non"])
            MonthlyCharges = st.number_input("Frais mensuels (F CFA)", 0.0, 200000.0, 20000.0, 1000.0, format="%.0f")
        with c_bill[1]:
            PaymentMethod = st.selectbox("Mode de paiement", [
                "Wave / Orange Money", "Chèque envoyé par courrier",
                "Virement bancaire automatique", "Carte bancaire (prélèvement automatique)",
            ])
            TotalCharges = st.number_input("Total déjà payé (F CFA)", 0.0, 10000000.0, 200000.0, 10000.0, format="%.0f")

        st.markdown("**📞 Téléphonie**")
        c_tel = st.columns(2)
        with c_tel[0]:
            PhoneService = st.selectbox("Ligne téléphonique ?", ["Oui", "Non"])
        with c_tel[1]:
            MultipleLines = st.selectbox("Plusieurs lignes ?", ["Pas de ligne", "Non", "Oui"])

        with st.expander("🌐 Services Internet", expanded=True):
            InternetService = st.selectbox("Connexion", ["ADSL/DSL", "Fibre optique", "Pas d'Internet"])
            c_svc = st.columns(2)
            with c_svc[0]:
                OnlineSecurity = st.selectbox("Sécurité en ligne", ["Pas d'Internet", "Non", "Oui"])
                OnlineBackup = st.selectbox("Sauvegarde en ligne", ["Pas d'Internet", "Non", "Oui"])
                DeviceProtection = st.selectbox("Protection appareil", ["Pas d'Internet", "Non", "Oui"])
            with c_svc[1]:
                TechSupport = st.selectbox("Support technique", ["Pas d'Internet", "Non", "Oui"])
                StreamingTV = st.selectbox("TV en streaming", ["Pas d'Internet", "Non", "Oui"])
                StreamingMovies = st.selectbox("Films en streaming", ["Pas d'Internet", "Non", "Oui"])

        submitted = st.form_submit_button("Analyser ce client", use_container_width=True)

    MAPPINGS = {
        "gender": lambda v: "Male" if v == "Homme" else "Female",
        "yn": lambda v: "Yes" if v == "Oui" else "No",
        "contract": {"Mensuel (sans engagement)": "Month-to-month",
                     "Engagement 1 an": "One year", "Engagement 2 ans": "Two year"},
        "payment": {"Wave / Orange Money": "Electronic check",
                    "Chèque envoyé par courrier": "Mailed check",
                    "Virement bancaire automatique": "Bank transfer (automatic)",
                    "Carte bancaire (prélèvement automatique)": "Credit card (automatic)"},
        "multiline": {"Pas de ligne": "No phone service", "Non": "No", "Oui": "Yes"},
        "internet": {"ADSL/DSL": "DSL", "Fibre optique": "Fiber optic", "Pas d'Internet": "No"},
        "service": {"Pas d'Internet": "No internet service", "Non": "No", "Oui": "Yes"},
    }
    def yn(v): return MAPPINGS["yn"](v)

    if submitted:
        payload = {
            "gender": MAPPINGS["gender"](gender),
            "SeniorCitizen": SeniorCitizen,
            "Partner": yn(Partner),
            "Dependents": yn(Dependents),
            "tenure": tenure,
            "PhoneService": yn(PhoneService),
            "MultipleLines": MAPPINGS["multiline"][MultipleLines],
            "InternetService": MAPPINGS["internet"][InternetService],
            "OnlineSecurity": MAPPINGS["service"][OnlineSecurity],
            "OnlineBackup": MAPPINGS["service"][OnlineBackup],
            "DeviceProtection": MAPPINGS["service"][DeviceProtection],
            "TechSupport": MAPPINGS["service"][TechSupport],
            "StreamingTV": MAPPINGS["service"][StreamingTV],
            "StreamingMovies": MAPPINGS["service"][StreamingMovies],
            "Contract": MAPPINGS["contract"][Contract],
            "PaperlessBilling": yn(PaperlessBilling),
            "PaymentMethod": MAPPINGS["payment"][PaymentMethod],
            "MonthlyCharges": round(MonthlyCharges / XOF_PER_USD, 2),
            "TotalCharges": round(TotalCharges / XOF_PER_USD, 2),
        }

        try:
            with st.spinner("Analyse en cours..."):
                resp = requests.post(f"{API_URL}/predict", json=payload, timeout=10)

            if resp.status_code == 200:
                result = resp.json()
                proba = result["churn_probability"]
                score = result.get("risk_score", proba * 100)
                is_risk = result["churn_prediction"] == 1

                color = "#dc2626" if is_risk else "#16a34a"
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=score,
                    number={"suffix": "%", "font": {"size": 40, "color": color, "family": "Inter"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#cbd5e1"},
                        "bar": {"color": color, "thickness": 0.25},
                        "bgcolor": "white", "borderwidth": 0,
                        "steps": [
                            {"range": [0, 40], "color": "#f1f5f9"},
                            {"range": [40, 70], "color": "#f1f5f9"},
                            {"range": [70, 100], "color": "#f1f5f9"},
                        ],
                        "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": score},
                    },
                ))
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=10, b=10),
                                  paper_bgcolor="rgba(0,0,0,0)", font={"family": "Inter"})

                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                if is_risk:
                    st.markdown(
                        f'<div class="result-card risk">'
                        f'<div><h3 style="color:var(--danger);">Risque élevé</h3>'
                        f'<p style="margin:6px 0;">Probabilité de départ : <strong>{score:.1f}%</strong></p>'
                        f'</div></div>', unsafe_allow_html=True)
                    st.warning("Proposer une offre de fidélisation ou un engagement avantage tarifaire.")
                else:
                    st.markdown(
                        f'<div class="result-card stable">'
                        f'<div><h3 style="color:var(--success);">Client stable</h3>'
                        f'<p style="margin:6px 0;">Probabilité de départ : <strong>{score:.1f}%</strong></p>'
                        f'</div></div>', unsafe_allow_html=True)

                record = {
                    "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "gender": gender, "senior": SeniorCitizen, "partner": Partner,
                    "dependents": Dependents, "tenure": tenure,
                    "contract": Contract, "payment": PaymentMethod,
                    "monthly": MonthlyCharges, "total": TotalCharges,
                    "churn_prediction": result["churn_prediction"],
                    "churn_probability": proba, "risk_score": score,
                    "statut": "Risque élevé" if is_risk else "Stable",
                }
                try:
                    requests.post(f"{API_URL}/history", json=record, timeout=5)
                except Exception:
                    pass
                st.session_state.history.append(record)
                df_new = pd.DataFrame([record])
                st.session_state.history_df = pd.concat([st.session_state.history_df, df_new], ignore_index=True)
            else:
                st.error(f"Erreur API ({resp.status_code}) : {resp.json().get('detail', '')}")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Impossible de se connecter à l'API.")
        except requests.exceptions.Timeout:
            st.error("⚠️ L'API n'a pas répondu à temps.")
        except Exception as e:
            st.error(f"⚠️ Erreur : {e}")

# ==============================
# TAB: ANALYSES
# ==============================
with tab_analyses:
    st.markdown(f'<div class="section-header">{icon("chart")} Analyse des prédictions</div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.info("💡 Aucune donnée pour le moment. Effectue d'abord des prédictions.")
        st.stop()

    df = st.session_state.history_df

    total = len(df)
    n_risky = int(df["churn_prediction"].sum())
    n_stable = total - n_risky
    avg_risk = df["risk_score"].mean()

    ka, kb = st.columns(2)
    with ka:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{icon("users")} Total</div>'
                    f'<div class="kpi-value">{total}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{icon("check")} Stable</div>'
                    f'<div class="kpi-value" style="color:var(--success);">{n_stable}</div>'
                    f'<div class="kpi-sub">{n_stable/total*100:.0f}%</div></div>', unsafe_allow_html=True)
    with kb:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{icon("alert")} Risque élevé</div>'
                    f'<div class="kpi-value" style="color:var(--danger);">{n_risky}</div>'
                    f'<div class="kpi-sub">{n_risky/total*100:.0f}%</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">{icon("trend")} Risque moyen</div>'
                    f'<div class="kpi-value">{avg_risk:.1f}%</div></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        contract_dist = df["contract"].value_counts()
        fig1 = px.bar(contract_dist, orientation="h",
                      labels={"value": "Clients", "index": "Contrat"},
                      color_discrete_sequence=["#1c3d5a"])
        fig1.update_layout(title="Répartition par contrat", height=240, margin=dict(l=0, r=0, t=40, b=0),
                           showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        payment_dist = df["payment"].value_counts()
        fig2 = px.pie(values=payment_dist.values, names=payment_dist.index,
                      color_discrete_sequence=["#1c3d5a", "#64748b", "#94a3b8", "#cbd5e1"])
        fig2.update_layout(title="Mode de paiement", height=240, margin=dict(l=0, r=0, t=40, b=0),
                           paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown(f'<div class="section-header">{icon("list")} Historique complet</div>', unsafe_allow_html=True)
    display_cols = ["date", "contract", "tenure", "payment", "monthly", "risk_score", "statut"]
    rename_map = {"date": "Date", "contract": "Contrat", "tenure": "Mois",
                  "payment": "Paiement", "monthly": "Mensuel", "risk_score": "Risque", "statut": "Statut"}
    df_display = df[display_cols].copy()
    df_display["monthly"] = df_display["monthly"].apply(lambda x: f"{x:,.0f} F CFA")
    df_display["risk_score"] = df_display["risk_score"].apply(lambda x: f"{x:.1f}%")
    df_display = df_display.rename(columns=rename_map)

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Télécharger (CSV)", data=csv, file_name="churn_predictions.csv",
                       mime="text/csv", use_container_width=True)
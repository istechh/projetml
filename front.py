import streamlit as st
import requests
import os
import plotly.graph_objects as go
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "https://projetchurn.onrender.com").rstrip("/")
XOF_PER_USD = 600  # 1 USD ≈ 600 F CFA (taux indicatif Sénégal)

st.set_page_config(
    page_title="Dashboard Churn Client",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# ICONES SVG (style "produit" — inspirées des dashboards churn / CRM réels)
# ---------------------------------------------------------------------------
ICONS = {
    "logo": """<svg width="42" height="42" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21" stroke="#1a73e8" stroke-width="2" stroke-linecap="round"/>
        <path d="M12 21C9.5 21 7.2 19.9 5.6 18.1" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-dasharray="1 4"/>
        <path d="M12 7V12L15 15" stroke="#1a3c6e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>""",
    "user": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 12C14.2091 12 16 10.2091 16 8C16 5.79086 14.2091 4 12 4C9.79086 4 8 5.79086 8 8C8 10.2091 9.79086 12 12 12Z" stroke="#1a3c6e" stroke-width="1.8"/><path d="M4 20C4 16.6863 7.58172 14 12 14C16.4183 14 20 16.6863 20 20" stroke="#1a3c6e" stroke-width="1.8" stroke-linecap="round"/></svg>""",
    "wifi": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M5 8.5C9.5 4.5 14.5 4.5 19 8.5" stroke="#1a3c6e" stroke-width="1.8" stroke-linecap="round"/><path d="M7.8 11.8C10.7 9.3 13.3 9.3 16.2 11.8" stroke="#1a3c6e" stroke-width="1.8" stroke-linecap="round"/><path d="M10.5 15C11.9 13.9 12.1 13.9 13.5 15" stroke="#1a3c6e" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="18" r="1.2" fill="#1a3c6e"/></svg>""",
    "shield": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M12 3L19 6V11C19 15.4 16 19.3 12 21C8 19.3 5 15.4 5 11V6L12 3Z" stroke="#1a3c6e" stroke-width="1.8" stroke-linejoin="round"/></svg>""",
    "card": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><rect x="3" y="6" width="18" height="12" rx="2" stroke="#1a3c6e" stroke-width="1.8"/><path d="M3 10H21" stroke="#1a3c6e" stroke-width="1.8"/></svg>""",
    "chart": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M4 20V10" stroke="#1a3c6e" stroke-width="1.8" stroke-linecap="round"/><path d="M10 20V4" stroke="#1a3c6e" stroke-width="1.8" stroke-linecap="round"/><path d="M16 20V13" stroke="#1a3c6e" stroke-width="1.8" stroke-linecap="round"/><path d="M2 20H22" stroke="#1a3c6e" stroke-width="1.8" stroke-linecap="round"/></svg>""",
    "alert": """<svg width="26" height="26" viewBox="0 0 24 24" fill="none"><path d="M12 9V13" stroke="#c62828" stroke-width="2.2" stroke-linecap="round"/><circle cx="12" cy="16.5" r="1" fill="#c62828"/><path d="M10.6 4.7C11.2 3.6 12.8 3.6 13.4 4.7L20.5 17.5C21.1 18.6 20.3 20 19 20H5C3.7 20 2.9 18.6 3.5 17.5L10.6 4.7Z" stroke="#c62828" stroke-width="1.8" stroke-linejoin="round"/></svg>""",
    "check": """<svg width="26" height="26" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="#2e7d32" stroke-width="1.8"/><path d="M8 12.5L10.7 15L16 9" stroke="#2e7d32" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>""",
}

def icon(name: str) -> str:
    return ICONS.get(name, "")

# ---------------------------------------------------------------------------
# STYLE
# ---------------------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background: linear-gradient(180deg, #f7f9fc 0%, #eef2f8 100%); }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 780px; }
    h1 { color: #1a3c6e; }

    /* Header brand bar */
    .brand-bar {
        display: flex; align-items: center; gap: 12px;
        padding: 14px 20px; background: white; border-radius: 14px;
        box-shadow: 0 2px 10px rgba(26,60,110,0.07);
        margin-bottom: 18px; border: 1px solid #eef1f6;
    }
    .brand-title { font-weight: 700; font-size: 1.15rem; color: #1a3c6e; margin: 0; }
    .brand-sub { font-size: 0.82rem; color: #6b7a90; margin: 0; }

    .stForm {
        background-color: white; padding: 28px 28px 12px 28px; border-radius: 16px;
        box-shadow: 0 4px 16px rgba(26,60,110,0.06);
        border: 1px solid #eef1f6;
        transition: box-shadow 0.25s ease;
    }
    .stForm:hover { box-shadow: 0 6px 22px rgba(26,60,110,0.10); }

    div[data-testid="stMetric"] {
        background-color: white; padding: 15px; border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    div[data-testid="stMetric"]:hover { transform: translateY(-2px); }

    .section-title {
        display: flex; align-items: center; gap: 8px;
        font-weight: 600; color: #1a3c6e; margin: 6px 0 12px 0; font-size: 1.02rem;
    }

    .result-card {
        padding: 24px; border-radius: 16px; margin-top: 20px;
        border-left: 6px solid; display: flex; align-items: center; gap: 18px;
        animation: fadeInUp 0.45s ease;
    }
    .result-card.stable { background-color: #eef8ef; border-color: #2e7d32; }
    .result-card.risk { background-color: #fdeeee; border-color: #c62828; }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .api-info {
        background-color: #eef4ff; padding: 10px 16px; border-radius: 10px;
        margin-bottom: 18px; font-size: 0.87rem; border-left: 4px solid #1a73e8;
        display: flex; align-items: center; gap: 8px;
    }

    /* Boutons plus fluides */
    .stButton>button, .stFormSubmitButton>button {
        border-radius: 10px !important;
        background: linear-gradient(90deg, #1a73e8, #1a3c6e) !important;
        color: white !important; border: none !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
        font-weight: 600 !important;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(26,115,232,0.35) !important;
    }

    /* Status dot */
    .status-dot {
        width: 9px; height: 9px; border-radius: 50%; display: inline-block;
        margin-right: 6px; box-shadow: 0 0 0 3px rgba(46,125,50,0.15);
    }
    .status-dot.online { background: #2e7d32; }
    .status-dot.offline { background: #c62828; box-shadow: 0 0 0 3px rgba(198,40,40,0.15); }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# HEADER / BRAND
# ---------------------------------------------------------------------------
st.markdown(
    f'''<div class="brand-bar">
        {icon("logo")}
        <div>
            <p class="brand-title">Churn Intelligence</p>
            <p class="brand-sub">Analyse prédictive du risque de départ client</p>
        </div>
    </div>''',
    unsafe_allow_html=True,
)

st.write("Renseignez les informations du client ci-dessous pour évaluer la probabilité qu'il quitte l'entreprise.")

# --- Health check & infos API ---
api_ok = False
api_info = None
try:
    r = requests.get(f"{API_URL}/", timeout=5)
    if r.status_code == 200:
        api_info = r.json()
        api_ok = True
except Exception:
    pass

if not api_ok:
    st.markdown(
        '<span class="status-dot offline"></span>**API indisponible**',
        unsafe_allow_html=True,
    )
    st.error(f"⚠️ Impossible de contacter l'API sur {API_URL}. Vérifiez que `uvicorn app:app` est lancé.")
    st.stop()

if api_info:
    st.markdown(
        f'<div class="api-info">'
        f'<span class="status-dot online"></span>'
        f"🧠 Modèle : <strong>{api_info.get('model_type', 'N/A')}</strong> &nbsp;·&nbsp; "
        f"ROC-AUC : <strong>{api_info.get('model_roc_auc', 'N/A')}</strong> &nbsp;·&nbsp; "
        f"Version API : <strong>{api_info.get('version', 'N/A')}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

with st.form("churn_form"):
    st.markdown(f'<div class="section-title">{icon("user")} Profil & Contrat</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        gender = st.selectbox("Sexe", ["Homme", "Femme"])
        SeniorCitizen = st.selectbox("Âge", [0, 1], format_func=lambda x: "Moins de 65 ans" if x == 0 else "65 ans ou plus")
        Partner = st.selectbox("En couple ?", ["Oui", "Non"])
        Dependents = st.selectbox("Personnes à charge ?", ["Oui", "Non"])
        Contract = st.selectbox("Type de contrat", [
            "Mensuel (sans engagement)", "Engagement 1 an", "Engagement 2 ans"
        ])
        PaperlessBilling = st.selectbox("Facture dématérialisée ?", ["Oui", "Non"])
        PaymentMethod = st.selectbox("Mode de paiement", [
            "Wave / Orange Money",
            "Chèque envoyé par courrier",
            "Virement bancaire automatique",
            "Carte bancaire (prélèvement automatique)",
        ])

    with col2:
        tenure = st.slider("Ancienneté (en mois)", min_value=0, max_value=100, value=12,
                           help="Depuis combien de mois le client est-il chez nous ?")
        MonthlyCharges = st.number_input("Frais mensuels (F CFA)", min_value=0.0, value=20000.0, step=1000.0, format="%.0f")
        TotalCharges = st.number_input("Total déjà payé (F CFA)", min_value=0.0, value=200000.0, step=10000.0, format="%.0f")
        PhoneService = st.selectbox("Ligne téléphonique ?", ["Oui", "Non"])
        if PhoneService == "Non":
            st.session_state["_multiline"] = "Pas de ligne"
        MultipleLines = st.selectbox(
            "Plusieurs lignes ?",
            ["Pas de ligne", "Non", "Oui"],
            disabled=PhoneService == "Non",
            key="_multiline",
            help="Se désactive et se réinitialise à 'Pas de ligne' quand 'Ligne téléphonique' est sur 'Non'.",
        )
        InternetService = st.selectbox("Connexion Internet", ["ADSL/DSL", "Fibre optique", "Pas d'Internet"])

    st.markdown(f'<div class="section-title">{icon("wifi")} Services additionnels</div>', unsafe_allow_html=True)
    col3, col4 = st.columns(2)
    with col3:
        OnlineSecurity = st.selectbox("Sécurité en ligne", ["Pas d'Internet", "Non", "Oui"])
        OnlineBackup = st.selectbox("Sauvegarde en ligne", ["Pas d'Internet", "Non", "Oui"])
        DeviceProtection = st.selectbox("Protection appareil", ["Pas d'Internet", "Non", "Oui"])
    with col4:
        TechSupport = st.selectbox("Support technique", ["Pas d'Internet", "Non", "Oui"])
        StreamingTV = st.selectbox("TV en streaming", ["Pas d'Internet", "Non", "Oui"])
        StreamingMovies = st.selectbox("Films en streaming", ["Pas d'Internet", "Non", "Oui"])

    submit_button = st.form_submit_button(label="🔍 Analyser ce client", use_container_width=True)

MAPPINGS = {
    "gender": lambda v: "Male" if v == "Homme" else "Female",
    "yn": lambda v: "Yes" if v == "Oui" else "No",
    "contract": {
        "Mensuel (sans engagement)": "Month-to-month",
        "Engagement 1 an": "One year",
        "Engagement 2 ans": "Two year",
    },
    "payment": {
        "Wave / Orange Money": "Electronic check",
        "Chèque envoyé par courrier": "Mailed check",
        "Virement bancaire automatique": "Bank transfer (automatic)",
        "Carte bancaire (prélèvement automatique)": "Credit card (automatic)",
    },
    "multiline": {
        "Pas de ligne": "No phone service",
        "Non": "No",
        "Oui": "Yes",
    },
    "internet": {
        "ADSL/DSL": "DSL",
        "Fibre optique": "Fiber optic",
        "Pas d'Internet": "No",
    },
    "service": {
        "Pas d'Internet": "No internet service",
        "Non": "No",
        "Oui": "Yes",
    },
}

def yn(val):
    return MAPPINGS["yn"](val)


def make_gauge(score: float, is_risk: bool) -> go.Figure:
    """Jauge de risque façon dashboard churn (Salesforce / HubSpot style)."""
    color = "#c62828" if is_risk else "#2e7d32"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"size": 42, "color": color, "family": "Inter"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#c8d1e0"},
                "bar": {"color": color, "thickness": 0.28},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "#eaf6ea"},
                    {"range": [40, 70], "color": "#fff4e0"},
                    {"range": [70, 100], "color": "#fce8e8"},
                ],
                "threshold": {
                    "line": {"color": color, "width": 4},
                    "thickness": 0.8,
                    "value": score,
                },
            },
        )
    )
    fig.update_layout(
        height=230,
        margin=dict(l=20, r=20, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter"},
    )
    return fig


if submit_button:
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
        with st.spinner("🔎 Analyse en cours..."):
            response = requests.post(f"{API_URL}/predict", json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            proba = result["churn_probability"]
            score = result.get("risk_score", proba * 100)
            is_risk = result["churn_prediction"] == 1

            st.markdown("---")
            st.markdown(f'<div class="section-title">{icon("chart")} Résultat de l\'analyse</div>', unsafe_allow_html=True)

            st.plotly_chart(make_gauge(score, is_risk), use_container_width=True, config={"displayModeBar": False})

            if is_risk:
                st.markdown(
                    f'<div class="result-card risk">'
                    f'{icon("alert")}'
                    f'<div>'
                    f'<h3 style="color:#c62828;margin:0;">Risque élevé de départ</h3>'
                    f'<p style="margin:6px 0 0 0;color:#4a4a4a;">Probabilité de départ estimée par le modèle : <strong>{score:.1f}%</strong></p>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.warning("💡 **Action recommandée** : proposer une offre de fidélisation ou un engagement avec avantage tarifaire.")
            else:
                st.markdown(
                    f'<div class="result-card stable">'
                    f'{icon("check")}'
                    f'<div>'
                    f'<h3 style="color:#2e7d32;margin:0;">Client stable</h3>'
                    f'<p style="margin:6px 0 0 0;color:#4a4a4a;">Probabilité de départ estimée par le modèle : <strong>{score:.1f}%</strong></p>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            detail = response.json().get("detail", "")
            st.error(f"Erreur API (code {response.status_code}) : {detail}")

    except requests.exceptions.ConnectionError:
        st.error(f"⚠️ Impossible de se connecter à l'API sur {API_URL}. Vérifiez que `uvicorn app:app` est lancé.")
    except requests.exceptions.Timeout:
        st.error("⚠️ L'API n'a pas répondu à temps. Réessayez.")
    except Exception as e:
        st.error(f"⚠️ Erreur inattendue : {e}")
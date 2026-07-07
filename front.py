import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "https://projetchurn.onrender.com").rstrip("/")

st.set_page_config(
    page_title="Dashboard Churn Client",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
    <style>
    .main { background-color: #f7f9fc; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    h1 { color: #1a3c6e; }
    .stForm { background-color: white; padding: 25px 25px 10px 25px; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
    div[data-testid="stMetric"] { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .stSubheader, .stMarkdown h3 { color: #1a3c6e; }
    .result-card {
        padding: 20px; border-radius: 12px; margin-top: 20px;
        border-left: 5px solid;
    }
    .result-card.stable { background-color: #e8f5e9; border-color: #2e7d32; }
    .result-card.risk { background-color: #ffebee; border-color: #c62828; }
    .api-info { background-color: #e3f2fd; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; font-size: 0.9rem; border-left: 4px solid #1a73e8; }
    </style>
""", unsafe_allow_html=True)

st.title("🔮 Analyse du Risque de Départ Client")
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
    st.error(f"⚠️ Impossible de contacter l'API sur {API_URL}. Vérifiez que `uvicorn app:app` est lancé.")
    st.stop()

if api_info:
    st.markdown(
        f'<div class="api-info">'
        f"🧠 Modèle : <strong>{api_info.get('model_type', 'N/A')}</strong> &nbsp;·&nbsp; "
        f"ROC-AUC : <strong>{api_info.get('model_roc_auc', 'N/A')}</strong> &nbsp;·&nbsp; "
        f"Version API : <strong>{api_info.get('version', 'N/A')}</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

with st.form("churn_form"):
    st.subheader("👤 Profil & Contrat")

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
        MonthlyCharges = st.number_input("Frais mensuels (€)", min_value=0.0, value=30.0, step=1.0)
        TotalCharges = st.number_input("Total déjà payé (€)", min_value=0.0, value=360.0, step=10.0)
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

    st.subheader("📡 Services additionnels")
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
        "MonthlyCharges": MonthlyCharges,
        "TotalCharges": TotalCharges,
    }

    try:
        with st.spinner("Analyse en cours..."):
            response = requests.post(f"{API_URL}/predict", json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            proba = result["churn_probability"]
            score = result.get("risk_score", proba * 100)

            st.markdown("---")
            st.markdown("### 📊 Résultat de l'analyse")

            if result["churn_prediction"] == 1:
                st.markdown(
                    f'<div class="result-card risk">'
                    f'<h3 style="color:#c62828;margin:0;">🚨 Risque élevé de départ</h3>'
                    f'<p style="font-size:2rem;font-weight:bold;margin:10px 0;color:#c62828;">{score:.1f}%</p>'
                    f'<p>Probabilité de départ estimée par le modèle.</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.warning("💡 **Action recommandée** : proposer une offre de fidélisation ou un engagement avec avantage tarifaire.")
            else:
                st.markdown(
                    f'<div class="result-card stable">'
                    f'<h3 style="color:#2e7d32;margin:0;">✅ Client stable</h3>'
                    f'<p style="font-size:2rem;font-weight:bold;margin:10px 0;color:#2e7d32;">{score:.1f}%</p>'
                    f'<p>Probabilité de départ estimée par le modèle.</p>'
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

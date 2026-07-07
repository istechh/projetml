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
    initial_sidebar_state="expanded",
)

ICONS = {
    "logo": """<svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12C21 16.9706 16.9706 21 12 21" stroke="#1a73e8" stroke-width="2" stroke-linecap="round"/>
        <path d="M12 21C9.5 21 7.2 19.9 5.6 18.1" stroke="#1a73e8" stroke-width="2" stroke-linecap="round" stroke-dasharray="1 4"/>
        <path d="M12 7V12L15 15" stroke="#1a3c6e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>""",
}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.main > .block-container { padding: 1.5rem 2rem; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1a2e 0%, #1a3c6e 100%);
}
[data-testid="stSidebar"] .sidebar-content { padding: 1.5rem 1rem; }
.sidebar-brand {
    display: flex; align-items: center; gap: 10px;
    padding: 0 0 20px 10px; border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 20px;
}
.sidebar-brand h2 { color: white; font-size: 1.1rem; margin: 0; font-weight: 700; }
.sidebar-brand p { color: rgba(255,255,255,0.5); font-size: 0.75rem; margin: 0; }

.stButton > button[kind="secondary"] {
    background: transparent !important; border: none !important;
    color: rgba(255,255,255,0.7) !important; text-align: left !important;
    padding: 10px 14px !important; border-radius: 10px !important;
    font-weight: 500 !important; width: 100% !important;
    transition: all 0.2s ease;
}
.stButton > button[kind="secondary"]:hover {
    background: rgba(255,255,255,0.08) !important;
    color: white !important;
}
.stButton > button[kind="secondary"] p {
    font-size: 0.9rem !important;
}
div[data-testid="stSidebarNav"] { display: none; }

.kpi-card {
    background: white; padding: 18px 22px; border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #eef1f6;
}
.kpi-label { font-size: 0.8rem; color: #6b7a90; font-weight: 500; }
.kpi-value { font-size: 1.6rem; font-weight: 700; color: #1a3c6e; margin: 4px 0 0 0; }
.kpi-sub { font-size: 0.78rem; color: #8b9ab0; }

.section-header {
    font-size: 1.05rem; font-weight: 600; color: #1a3c6e;
    margin: 24px 0 14px 0; display: flex; align-items: center; gap: 8px;
}

.stForm {
    background: white; padding: 24px; border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04); border: 1px solid #eef1f6;
}

.result-card {
    padding: 20px 24px; border-radius: 14px; margin-top: 16px;
    border-left: 5px solid; display: flex; align-items: center; gap: 16px;
    animation: fadeIn 0.4s ease;
}
.result-card.risk { background: #fef2f2; border-color: #dc2626; }
.result-card.stable { background: #f0fdf4; border-color: #16a34a; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.api-badge {
    display: inline-flex; align-items: center; gap: 6px;
    background: #eef4ff; padding: 6px 14px; border-radius: 20px;
    font-size: 0.78rem; color: #1a3c6e; border: 1px solid #d6e4ff;
}
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.green { background: #16a34a; box-shadow: 0 0 0 3px rgba(22,163,74,0.15); }
.dot.red { background: #dc2626; box-shadow: 0 0 0 3px rgba(220,38,38,0.15); }

.history-table {
    background: white; border-radius: 14px; overflow: hidden;
    border: 1px solid #eef1f6;
}
</style>
""", unsafe_allow_html=True)

# --- Session state ---
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "history" not in st.session_state:
    st.session_state.history = []
if "history_df" not in st.session_state:
    st.session_state.history_df = pd.DataFrame()

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

# --- Sidebar ---
with st.sidebar:
    st.markdown(
        f'<div class="sidebar-brand">{ICONS["logo"]}<div><h2>Churn Intelligence</h2>'
        f'<p>Analyse prédictive client</p></div></div>',
        unsafe_allow_html=True,
    )
    if api_ok and api_info:
        st.markdown(
            f'<div style="padding:0 0 20px 10px;font-size:0.78rem;">'
            f'<span class="dot green"></span> API connectée &nbsp;·&nbsp; {api_info.get("model_type","")}'
            f'</div>', unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="padding:0 0 20px 10px;font-size:0.78rem;">'
            f'<span class="dot red"></span> API hors ligne'
            f'</div>', unsafe_allow_html=True,
        )

    for page_name in ["Dashboard", "Prédiction", "Analyses"]:
        if st.button(page_name, key=f"nav_{page_name}", help=f"Accéder à {page_name}"):
            st.session_state.page = page_name
            st.rerun()

    st.markdown(
        f'<div style="position:absolute;bottom:20px;left:20px;font-size:0.72rem;color:rgba(255,255,255,0.3);">'
        f'v2.0 · Sénégal</div>',
        unsafe_allow_html=True,
    )

# --- Pages ---
page = st.session_state.page

if page == "Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">👥 Total clients</div>'
                    f'<div class="kpi-value">{len(st.session_state.history) or "—"}</div>'
                    f'<div class="kpi-sub">analysés ce mois</div></div>', unsafe_allow_html=True)
    with col2:
        risky = sum(1 for h in st.session_state.history if h.get("churn_prediction") == 1)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">🚨 Risque élevé</div>'
                    f'<div class="kpi-value" style="color:#dc2626;">{risky or "—"}</div>'
                    f'<div class="kpi-sub">{f"{risky/len(st.session_state.history)*100:.0f}%" if st.session_state.history else ""}</div></div>', unsafe_allow_html=True)
    with col3:
        stable = sum(1 for h in st.session_state.history if h.get("churn_prediction") == 0)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">✅ Clients stables</div>'
                    f'<div class="kpi-value" style="color:#16a34a;">{stable or "—"}</div>'
                    f'<div class="kpi-sub">{f"{stable/len(st.session_state.history)*100:.0f}%" if st.session_state.history else ""}</div></div>', unsafe_allow_html=True)
    with col4:
        avg_risk = 0
        if st.session_state.history:
            avg_risk = sum(h.get("risk_score", 0) or h.get("churn_probability", 0) * 100 for h in st.session_state.history) / len(st.session_state.history)
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">📊 Risque moyen</div>'
                    f'<div class="kpi-value">{f"{avg_risk:.1f}%" if st.session_state.history else "—"}</div>'
                    f'<div class="kpi-sub">sur tous les clients</div></div>', unsafe_allow_html=True)

    if st.session_state.history:
        st.markdown('<div class="section-header">📈 Dernières analyses</div>', unsafe_allow_html=True)
        df_show = st.session_state.history_df.tail(5)[["date", "contract", "tenure", "monthly", "score", "statut"]].copy()
        df_show.columns = ["Date", "Contrat", "Ancienneté", "Mensuel", "Risque", "Statut"]
        df_show["Mensuel"] = df_show["Mensuel"].apply(lambda x: f"{x:,.0f} F CFA")
        df_show["Risque"] = df_show["Risque"].apply(lambda x: f"{x:.1f}%")
        st.dataframe(df_show, use_container_width=True, hide_index=True,
                     column_config={"Statut": st.column_config.Column(width="small")})
    else:
        st.info("💡 Aucune analyse pour l'instant. Va dans **Prédiction** pour évaluer un client.")

    if api_info:
        st.markdown(f'<div style="margin-top:24px;font-size:0.8rem;color:#6b7a90;">'
                    f'🧠 Modèle : {api_info.get("model_type")} · '
                    f'ROC-AUC : {api_info.get("model_roc_auc")} · '
                    f'Version API : {api_info.get("version")}</div>', unsafe_allow_html=True)

elif page == "Prédiction":
    if not api_ok:
        st.error(f"⚠️ Impossible de contacter l'API sur {API_URL}. Vérifiez que l'API est lancée.")
        st.stop()

    with st.form("churn_form"):
        col_left, col_right = st.columns([1, 1])
        with col_left:
            st.markdown("**👤 Profil & Contrat**")
            gender = st.selectbox("Sexe", ["Homme", "Femme"])
            SeniorCitizen = st.selectbox("Tranche d'âge", [0, 1],
                                         format_func=lambda x: "Moins de 65 ans" if x == 0 else "65 ans ou plus")
            Partner = st.selectbox("En couple ?", ["Oui", "Non"])
            Dependents = st.selectbox("Personnes à charge ?", ["Oui", "Non"])
            Contract = st.selectbox("Type de contrat",
                                    ["Mensuel (sans engagement)", "Engagement 1 an", "Engagement 2 ans"])
            tenure = st.slider("Ancienneté (en mois)", 0, 100, 12)
        with col_right:
            st.markdown("**💳 Facturation**")
            PaperlessBilling = st.selectbox("Facture dématérialisée ?", ["Oui", "Non"])
            PaymentMethod = st.selectbox("Mode de paiement", [
                "Wave / Orange Money", "Chèque envoyé par courrier",
                "Virement bancaire automatique", "Carte bancaire (prélèvement automatique)",
            ])
            MonthlyCharges = st.number_input("Frais mensuels (F CFA)", 0.0, 200000.0, 20000.0, 1000.0, format="%.0f")
            TotalCharges = st.number_input("Total déjà payé (F CFA)", 0.0, 10000000.0, 200000.0, 10000.0, format="%.0f")

        st.markdown("---")
        col_tel, col_inet = st.columns([1, 1])
        with col_tel:
            st.markdown("**📞 Téléphonie**")
            PhoneService = st.selectbox("Ligne téléphonique ?", ["Oui", "Non"])
            MultipleLines = st.selectbox("Plusieurs lignes ?",
                                         ["Pas de ligne", "Non", "Oui"],
                                         disabled=PhoneService == "Non")
        with col_inet:
            st.markdown("**🌐 Internet**")
            InternetService = st.selectbox("Connexion", ["ADSL/DSL", "Fibre optique", "Pas d'Internet"])
            disabled_svc = InternetService == "Pas d'Internet"
            OnlineSecurity = st.selectbox("Sécurité en ligne", ["Pas d'Internet", "Non", "Oui"], disabled=disabled_svc)
            OnlineBackup = st.selectbox("Sauvegarde en ligne", ["Pas d'Internet", "Non", "Oui"], disabled=disabled_svc)
            DeviceProtection = st.selectbox("Protection appareil", ["Pas d'Internet", "Non", "Oui"], disabled=disabled_svc)
            TechSupport = st.selectbox("Support technique", ["Pas d'Internet", "Non", "Oui"], disabled=disabled_svc)
            StreamingTV = st.selectbox("TV en streaming", ["Pas d'Internet", "Non", "Oui"], disabled=disabled_svc)
            StreamingMovies = st.selectbox("Films en streaming", ["Pas d'Internet", "Non", "Oui"], disabled=disabled_svc)

        submitted = st.form_submit_button("🔍 Analyser ce client", use_container_width=True)

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
            with st.spinner("🔎 Analyse en cours..."):
                resp = requests.post(f"{API_URL}/predict", json=payload, timeout=10)

            if resp.status_code == 200:
                result = resp.json()
                proba = result["churn_probability"]
                score = result.get("risk_score", proba * 100)
                is_risk = result["churn_prediction"] == 1

                color = "#dc2626" if is_risk else "#16a34a"
                fig = go.Figure(go.Indicator(
                    mode="gauge+number", value=score,
                    number={"suffix": "%", "font": {"size": 44, "color": color, "family": "Inter"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#c8d1e0"},
                        "bar": {"color": color, "thickness": 0.25},
                        "bgcolor": "white", "borderwidth": 0,
                        "steps": [
                            {"range": [0, 40], "color": "#f0fdf4"},
                            {"range": [40, 70], "color": "#fefce8"},
                            {"range": [70, 100], "color": "#fef2f2"},
                        ],
                        "threshold": {"line": {"color": color, "width": 4}, "thickness": 0.8, "value": score},
                    },
                ))
                fig.update_layout(height=210, margin=dict(l=20, r=20, t=10, b=10),
                                  paper_bgcolor="rgba(0,0,0,0)", font={"family": "Inter"})

                col_g, col_info = st.columns([1, 1.2])
                with col_g:
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                with col_info:
                    if is_risk:
                        st.markdown(
                            f'<div class="result-card risk">'
                            f'<div><h3 style="color:#dc2626;margin:0;">🚨 Risque élevé</h3>'
                            f'<p style="margin:6px 0;color:#4a4a4a;">Probabilité de départ : <strong>{score:.1f}%</strong></p>'
                            f'</div></div>', unsafe_allow_html=True)
                        st.warning("💡 Proposer une offre de fidélisation ou un engagement avantage tarifaire.")
                    else:
                        st.markdown(
                            f'<div class="result-card stable">'
                            f'<div><h3 style="color:#16a34a;margin:0;">✅ Client stable</h3>'
                            f'<p style="margin:6px 0;color:#4a4a4a;">Probabilité de départ : <strong>{score:.1f}%</strong></p>'
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
                st.session_state.history.append(record)
                df_new = pd.DataFrame([record])
                st.session_state.history_df = pd.concat([st.session_state.history_df, df_new], ignore_index=True)
            else:
                st.error(f"Erreur API ({resp.status_code}) : {resp.json().get('detail', '')}")
        except requests.exceptions.ConnectionError:
            st.error(f"⚠️ Impossible de se connecter à l'API.")
        except requests.exceptions.Timeout:
            st.error("⚠️ L'API n'a pas répondu à temps.")
        except Exception as e:
            st.error(f"⚠️ Erreur : {e}")

elif page == "Analyses":
    st.markdown('<div class="section-header">📊 Analyse des prédictions</div>', unsafe_allow_html=True)

    if not st.session_state.history:
        st.info("💡 Aucune donnée pour le moment. Effectue d'abord des prédictions.")
        st.stop()

    df = st.session_state.history_df

    k1, k2, k3, k4 = st.columns(4)
    total = len(df)
    n_risky = df["churn_prediction"].sum()
    n_stable = total - n_risky
    avg_risk = df["risk_score"].mean()
    with k1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">👥 Total</div>'
                    f'<div class="kpi-value">{total}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">🚨 Risque élevé</div>'
                    f'<div class="kpi-value" style="color:#dc2626;">{n_risky}</div>'
                    f'<div class="kpi-sub">{n_risky/total*100:.0f}%</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">✅ Stable</div>'
                    f'<div class="kpi-value" style="color:#16a34a;">{n_stable}</div>'
                    f'<div class="kpi-sub">{n_stable/total*100:.0f}%</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">📊 Risque moyen</div>'
                    f'<div class="kpi-value">{avg_risk:.1f}%</div></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        contract_dist = df["contract"].value_counts()
        fig1 = px.bar(contract_dist, orientation="h",
                      labels={"value": "Clients", "index": "Contrat"},
                      color_discrete_sequence=["#1a3c6e"])
        fig1.update_layout(title="Répartition par contrat", height=240, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        payment_dist = df["payment"].value_counts()
        fig2 = px.pie(values=payment_dist.values, names=payment_dist.index,
                      color_discrete_sequence=px.colors.sequential.Blues_r)
        fig2.update_layout(title="Mode de paiement", height=240, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-header">📋 Historique complet</div>', unsafe_allow_html=True)
    display_cols = ["date", "contract", "tenure", "payment", "monthly", "risk_score", "statut"]
    rename_map = {"date": "Date", "contract": "Contrat", "tenure": "Mois",
                  "payment": "Paiement", "monthly": "Mensuel", "risk_score": "Risque", "statut": "Statut"}
    df_display = df[display_cols].copy()
    df_display["monthly"] = df_display["monthly"].apply(lambda x: f"{x:,.0f} F CFA")
    df_display["risk_score"] = df_display["risk_score"].apply(lambda x: f"{x:.1f}%")
    df_display = df_display.rename(columns=rename_map)

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("📥 Télécharger (CSV)", data=csv, file_name="churn_predictions.csv",
                       mime="text/csv", use_container_width=True)

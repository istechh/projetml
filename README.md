# Churn Intelligence — Analyse Prédictive du Départ Client

Application de prédiction du **churn client** (attrition) pour le secteur des télécommunications au Sénégal.  
Frontend Streamlit + API FastAPI + modèle Random Forest.

---

## 📊 Facteurs clés du départ client

### 🔴 Ce qui augmente le risque de départ

| Variable | Détail | Impact |
|---|---|---|
| **Contrat mensuel** | `Month-to-month` | **42,7%** de churn (vs 2,8% pour engagement 2 ans) |
| **Fibre optique** | `Fiber optic` | **41,9%** de churn (vs 7,4% sans internet) |
| **Paiement par Wave/Orange Money** | `Electronic check` | **45,3%** de churn (vs 15,2% carte bancaire) |
| **Frais mensuels élevés** | `MonthlyCharges` | Variable importante du modèle |
| **Nouveau client** | `tenure` faible | **1ʳᵉ variable** la plus importante du modèle |
| **Absence de sécurité en ligne** | `OnlineSecurity=No` | **41,8%** de churn |
| **Absence de support technique** | `TechSupport=No` | **41,6%** de churn |
| **Facture dématérialisée** | `PaperlessBilling=Yes` | **33,6%** de churn |
| **Seul(e)** | `Partner=No` | **33,0%** de churn |
| **Sans personne à charge** | `Dependents=No` | **31,3%** de churn |

### 🟢 Ce qui fidélise

| Variable | Détail | Taux de rétention |
|---|---|---|
| **Engagement 2 ans** | `Contract=Two year` | **97,2%** restent |
| **Paiement par carte bancaire** | `Credit card (automatic)` | **84,8%** restent |
| **Sécurité en ligne activée** | `OnlineSecurity=Yes` | **85,4%** restent |
| **Support technique activé** | `TechSupport=Yes` | **84,8%** restent |
| **Ancienneté élevée** | `tenure` élevé | Client de longue date = plus fidèle |
| **En couple** | `Partner=Yes` | **80,3%** restent |
| **Avec personnes à charge** | `Dependents=Yes` | **84,5%** restent |

---

## 🧠 Modèle

- **Algorithme** : Random Forest (200 arbres, profondeur max 10)
- **ROC-AUC** : 0.8443
- **Variables les plus importantes** :
  1. `tenure` (ancienneté) — 17,9%
  2. `TotalCharges` (total payé) — 13,5%
  3. `Contract_Two year` (engagement 2 ans) — 11,2%
  4. `MonthlyCharges` (frais mensuels) — 9,0%
  5. `InternetService_Fiber optic` (fibre) — 7,3%

---

## 🚀 Déploiement

- **API** : Render — `uvicorn app:app --host 0.0.0.0 --port $PORT`
- **Frontend** : Streamlit Cloud — `streamlit run front.py`
- **Variables d'environnement** : `API_URL=https://projetchurn.onrender.com`

## 📁 Structure

```
app.py              → API FastAPI
front.py            → Dashboard Streamlit
train.py            → Entraînement du modèle
requirements.txt    → Dépendances
Telco-Customer-Churn.csv  → Données d'entraînement
```

## 📌 Conversion CFA

Les montants sont saisis en **F CFA** et convertis automatiquement en USD (1 $ ≈ 600 F CFA) avant prédiction.

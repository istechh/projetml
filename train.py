import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import json
import os
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    roc_auc_score, precision_recall_curve, f1_score
)

DATA_PATH = os.getenv("DATA_PATH", "Telco-Customer-Churn.csv")
MODEL_PATH = os.getenv("MODEL_PATH", "modele_churn_telecom.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "scaler_churn.pkl")
RANDOM_STATE = 42

print("=" * 60)
print("CHURN TELECOM - PIPELINE D'ENTRAÎNEMENT")
print("=" * 60)

df = pd.read_csv(DATA_PATH)
print(f"\nDataset chargé : {df.shape[0]} lignes, {df.shape[1]} colonnes")

# Nettoyage
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
nulls = df['TotalCharges'].isnull().sum()
if nulls > 0:
    median_val = df['TotalCharges'].median()
    df['TotalCharges'] = df['TotalCharges'].fillna(median_val)
    print(f"Valeurs manquantes dans TotalCharges : {nulls} -> imputées par la médiane ({median_val:.2f})")

df['Churn_numeric'] = df['Churn'].map({'Yes': 1, 'No': 0})

print("\n--- Analyse exploratoire rapide ---")
print(df['Churn'].value_counts())
print(f"Taux de churn : {df['Churn_numeric'].mean():.1%}")

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
sns.countplot(data=df, x='Contract', hue='Churn', ax=axes[0])
axes[0].set_title('Churn par type de contrat')
sns.countplot(data=df, x='InternetService', hue='Churn', ax=axes[1])
axes[1].set_title('Churn par type d\'Internet')
plt.tight_layout()
plt.savefig('eda_churn.png', dpi=100)
print("Graphique EDA sauvegardé : eda_churn.png")

# Préparation des features
df_model = df.drop(columns=['customerID', 'Churn', 'Churn_numeric'], errors='ignore')

# Séparation AVANT encodage (pas de data leakage)
y = df['Churn_numeric']
X_train, X_test, y_train, y_test = train_test_split(
    df_model, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
)
print(f"\nTrain : {X_train.shape[0]} | Test : {X_test.shape[0]}")

# Encodage one-hot sur le train, puis alignement du test
X_train_encoded = pd.get_dummies(X_train, drop_first=True, dtype=int)
X_test_encoded = pd.get_dummies(X_test, drop_first=True, dtype=int)

# Alignement : le test doit avoir exactement les mêmes colonnes que le train
X_test_encoded = X_test_encoded.reindex(columns=X_train_encoded.columns, fill_value=0)

# Scaling des colonnes numériques
num_cols = ['tenure', 'MonthlyCharges', 'TotalCharges']
scaler = StandardScaler()

X_train_scaled = X_train_encoded.copy()
X_test_scaled = X_test_encoded.copy()

X_train_scaled[num_cols] = scaler.fit_transform(X_train_encoded[num_cols])
X_test_scaled[num_cols] = scaler.transform(X_test_encoded[num_cols])

print("\n" + "=" * 60)
print("ENTRAÎNEMENT DES MODÈLES")
print("=" * 60)

# --- Logistic Regression ---
print("\n>>> Régression Logistique (class_weight='balanced')")
lr = LogisticRegression(max_iter=1000, class_weight='balanced', random_state=RANDOM_STATE)
lr.fit(X_train_scaled, y_train)

y_pred_lr = lr.predict(X_test_scaled)
y_proba_lr = lr.predict_proba(X_test_scaled)[:, 1]

print(classification_report(y_test, y_pred_lr))
print(f"ROC-AUC : {roc_auc_score(y_test, y_proba_lr):.4f}")

cv_lr = cross_val_score(lr, X_train_scaled, y_train, cv=StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE), scoring='roc_auc')
print(f"ROC-AUC moyen (CV 5-fold) : {cv_lr.mean():.4f} (+/- {cv_lr.std():.4f})")

# --- Random Forest ---
print("\n>>> Random Forest (class_weight='balanced')")
rf = RandomForestClassifier(
    n_estimators=200, max_depth=10, min_samples_leaf=5,
    class_weight='balanced_subsample', random_state=RANDOM_STATE, n_jobs=-1
)
rf.fit(X_train_encoded, y_train)

y_pred_rf = rf.predict(X_test_encoded)
y_proba_rf = rf.predict_proba(X_test_encoded)[:, 1]

print(classification_report(y_test, y_pred_rf))
print(f"ROC-AUC : {roc_auc_score(y_test, y_proba_rf):.4f}")

cv_rf = cross_val_score(rf, X_train_encoded, y_train, cv=StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE), scoring='roc_auc')
print(f"ROC-AUC moyen (CV 5-fold) : {cv_rf.mean():.4f} (+/- {cv_rf.std():.4f})")

# --- Sélection du meilleur modèle ---
score_lr = roc_auc_score(y_test, y_proba_lr)
score_rf = roc_auc_score(y_test, y_proba_rf)

print("\n" + "=" * 60)
print("SÉLECTION DU MODÈLE CHAMPION")
print("=" * 60)

if score_lr >= score_rf:
    champion = lr
    champion_name = "Régression Logistique"
    champion_auc = score_lr
    print(f"Champion : {champion_name} (ROC-AUC: {champion_auc:.4f})")
    scaler_to_save = scaler
    features = list(X_train_encoded.columns)
    num_cols_to_scale = num_cols
else:
    champion = rf
    champion_name = "Random Forest"
    champion_auc = score_rf
    print(f"Champion : {champion_name} (ROC-AUC: {champion_auc:.4f})")
    scaler_to_save = None
    features = list(X_train_encoded.columns)
    num_cols_to_scale = num_cols

# Matrice de confusion du champion
print(f"\nMatrice de confusion ({champion_name}) :")
if champion_name == "Régression Logistique":
    y_pred_champ = champion.predict(X_test_scaled)
    cm = confusion_matrix(y_test, y_pred_champ)
else:
    y_pred_champ = champion.predict(X_test_encoded)
    cm = confusion_matrix(y_test, y_pred_champ)
print(cm)

# Sauvegarde
joblib.dump(champion, MODEL_PATH)
if scaler_to_save is not None:
    joblib.dump(scaler_to_save, SCALER_PATH)

# Sauvegarde des métadonnées pour l'API
metadata = {
    "model_type": champion_name,
    "features": features,
    "num_cols": num_cols_to_scale,
    "roc_auc": round(champion_auc, 4),
    "requires_scaler": scaler_to_save is not None,
}
with open("model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"\n✓ Modèle sauvegardé : {MODEL_PATH}")
if scaler_to_save is not None:
    print(f"✓ Scaler sauvegardé : {SCALER_PATH}")
print(f"✓ Métadonnées sauvegardées : model_metadata.json")
print(f"\n=== ENTRAÎNEMENT TERMINÉ ===")

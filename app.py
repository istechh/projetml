from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import joblib
import pandas as pd
import numpy as np
import json
import os
import sqlite3
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "modele_churn_telecom.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "scaler_churn.pkl")
METADATA_PATH = os.getenv("METADATA_PATH", "model_metadata.json")

app = FastAPI(title="API de Prédiction du Churn Telecom", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    model = joblib.load(MODEL_PATH)
    model_features = model.feature_names_in_
except Exception as e:
    raise RuntimeError(f"Impossible de charger le modèle depuis {MODEL_PATH}: {e}")

try:
    with open(METADATA_PATH) as f:
        metadata = json.load(f)
    requires_scaler = metadata.get("requires_scaler", False)
    num_cols = metadata.get("num_cols", ["tenure", "MonthlyCharges", "TotalCharges"])
except FileNotFoundError:
    requires_scaler = True
    num_cols = ["tenure", "MonthlyCharges", "TotalCharges"]

scaler = None
if requires_scaler:
    try:
        scaler = joblib.load(SCALER_PATH)
    except Exception as e:
        raise RuntimeError(f"Impossible de charger le scaler depuis {SCALER_PATH}: {e}")

DB_PATH = os.getenv("DB_PATH", "churn.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, gender TEXT, senior INTEGER,
            partner TEXT, dependents TEXT, tenure INTEGER,
            contract TEXT, payment TEXT, monthly REAL,
            total REAL, churn_prediction INTEGER,
            churn_probability REAL, risk_score REAL, statut TEXT
        )
    """)
    conn.commit()
    return conn

def _load_history():
    conn = get_db()
    rows = conn.execute("SELECT * FROM history ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def _save_record(record: dict):
    conn = get_db()
    conn.execute("""
        INSERT INTO history (date, gender, senior, partner, dependents,
            tenure, contract, payment, monthly, total,
            churn_prediction, churn_probability, risk_score, statut)
        VALUES (:date, :gender, :senior, :partner, :dependents,
            :tenure, :contract, :payment, :monthly, :total,
            :churn_prediction, :churn_probability, :risk_score, :statut)
    """, record)
    conn.commit()
    conn.close()

def _clear_history():
    conn = get_db()
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()

VALID_BOOLEAN = {"Yes", "No"}
VALID_GENDER = {"Male", "Female"}
VALID_PHONE = {"Yes", "No", "No phone service"}
VALID_INTERNET = {"DSL", "Fiber optic", "No"}
VALID_SERVICE = {"Yes", "No", "No internet service"}
VALID_CONTRACT = {"Month-to-month", "One year", "Two year"}
VALID_PAYMENT = {
    "Electronic check", "Mailed check",
    "Bank transfer (automatic)", "Credit card (automatic)"
}

class ClientInput(BaseModel):
    gender: str = Field(..., description="Male ou Female")
    SeniorCitizen: int = Field(..., ge=0, le=1)
    Partner: str = Field(..., description="Yes ou No")
    Dependents: str = Field(..., description="Yes ou No")
    tenure: int = Field(..., ge=0, le=100)
    PhoneService: str = Field(..., description="Yes ou No")
    MultipleLines: str = Field(..., description="Yes, No, ou No phone service")
    InternetService: str = Field(..., description="DSL, Fiber optic, ou No")
    OnlineSecurity: str = Field(..., description="Yes, No, ou No internet service")
    OnlineBackup: str = Field(..., description="Yes, No, ou No internet service")
    DeviceProtection: str = Field(..., description="Yes, No, ou No internet service")
    TechSupport: str = Field(..., description="Yes, No, ou No internet service")
    StreamingTV: str = Field(..., description="Yes, No, ou No internet service")
    StreamingMovies: str = Field(..., description="Yes, No, ou No internet service")
    Contract: str = Field(..., description="Month-to-month, One year, ou Two year")
    PaperlessBilling: str = Field(..., description="Yes ou No")
    PaymentMethod: str = Field(..., description="Electronic check, Mailed check, Bank transfer (automatic), ou Credit card (automatic)")
    MonthlyCharges: float = Field(..., ge=0)
    TotalCharges: float = Field(..., ge=0)

    @field_validator("gender")
    @classmethod
    def check_gender(cls, v):
        if v not in VALID_GENDER:
            raise ValueError(f"gender doit être l'un de {VALID_GENDER}")
        return v

    @field_validator("Partner", "Dependents", "PhoneService", "PaperlessBilling")
    @classmethod
    def check_boolean(cls, v):
        if v not in VALID_BOOLEAN:
            raise ValueError(f"La valeur doit être l'un de {VALID_BOOLEAN}")
        return v

    @field_validator("MultipleLines")
    @classmethod
    def check_multiline(cls, v):
        if v not in VALID_PHONE:
            raise ValueError(f"MultipleLines doit être l'un de {VALID_PHONE}")
        return v

    @field_validator("InternetService")
    @classmethod
    def check_internet(cls, v):
        if v not in VALID_INTERNET:
            raise ValueError(f"InternetService doit être l'un de {VALID_INTERNET}")
        return v

    @field_validator("OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies")
    @classmethod
    def check_service(cls, v):
        if v not in VALID_SERVICE:
            raise ValueError(f"La valeur doit être l'un de {VALID_SERVICE}")
        return v

    @field_validator("Contract")
    @classmethod
    def check_contract(cls, v):
        if v not in VALID_CONTRACT:
            raise ValueError(f"Contract doit être l'un de {VALID_CONTRACT}")
        return v

    @field_validator("PaymentMethod")
    @classmethod
    def check_payment(cls, v):
        if v not in VALID_PAYMENT:
            raise ValueError(f"PaymentMethod doit être l'un de {VALID_PAYMENT}")
        return v

@app.get("/")
def home():
    return {
        "message": "API de Prédiction du Churn Telecom opérationnelle.",
        "version": "2.0.0",
        "model_type": metadata.get("model_type", "unknown"),
        "model_roc_auc": metadata.get("roc_auc", "unknown"),
    }

class HistoryRecord(BaseModel):
    date: str
    gender: str
    senior: int
    partner: str
    dependents: str
    tenure: int
    contract: str
    payment: str
    monthly: float
    total: float
    churn_prediction: int
    churn_probability: float
    risk_score: float
    statut: str

class HistoryResponse(BaseModel):
    history: list
    count: int

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/history")
def get_history():
    data = _load_history()
    return HistoryResponse(history=data, count=len(data))

@app.post("/history")
def add_history(record: HistoryRecord):
    _save_record(record.model_dump())
    return {"status": "ok"}

@app.delete("/history")
def clear_history():
    _clear_history()
    return {"status": "ok", "message": "Historique effacé"}

@app.post("/predict")
def predict(client: ClientInput):
    try:
        client_dict = client.model_dump()
        df_client = pd.DataFrame([client_dict])

        df_encoded = pd.get_dummies(df_client, drop_first=True, dtype=int)
        X_custom = df_encoded.reindex(columns=model_features, fill_value=0)

        if scaler is not None:
            X_custom[num_cols] = scaler.transform(X_custom[num_cols])

        prediction = int(model.predict(X_custom)[0])
        probabilite = float(model.predict_proba(X_custom)[0][1])

        return {
            "churn_prediction": prediction,
            "churn_probability": round(probabilite, 4),
            "statut": "Risque élevé" if prediction == 1 else "Stable",
            "risk_score": round(probabilite * 100, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction : {str(e)}")

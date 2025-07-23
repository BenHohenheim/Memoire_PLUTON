from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import os

class PredictRequest(BaseModel):
    features: list[float]

class PredictResponse(BaseModel):
    label: str
    proba: float

app = FastAPI(title="PLUTON Inference API")

# Charge les pickles depuis le même dossier
MODEL_PATH   = os.path.join(os.path.dirname(__file__), "pluton_model.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "pluton_label_encoder.pkl")

model   = joblib.load(MODEL_PATH)
encoder = joblib.load(ENCODER_PATH)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    try:
        X = np.array(req.features).reshape(1, -1)
        proba_arr = model.predict_proba(X)[0]
        idx       = int(np.argmax(proba_arr))
        label     = encoder.inverse_transform([idx])[0]
        return {"label": label, "proba": float(proba_arr[idx])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""FastAPI service for predicting customer churn."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(PROJECT_ROOT / "model.joblib")))


class Customer(BaseModel):
    """One customer's features; field names match the trained model."""

    model_config = ConfigDict(extra="forbid")

    tenure_months: int = Field(ge=0, description="How many months the customer stayed")
    monthly_charges: float = Field(ge=0, description="Monthly bill amount")
    support_calls: int = Field(ge=0, description="Number of support calls")
    contract: Literal["month-to-month", "one-year", "two-year"]
    internet_service: Literal["dsl", "fiber", "none"]


@lru_cache(maxsize=1)
def load_model():
    """Load once and cache the fitted scikit-learn pipeline."""
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Model file is missing at {MODEL_PATH}. Run src/train/train.py first."
        )
    return joblib.load(MODEL_PATH)


app = FastAPI(title="AI381 Lab 2 Churn API", version="1.0.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Report healthy only when the model file can be loaded."""
    load_model()
    return {"status": "ok"}


@app.post("/predict")
def predict(customer: Customer) -> dict[str, float | int]:
    """Return churn probability and the 0/1 prediction at a 0.5 threshold."""
    model = load_model()
    features = pd.DataFrame(
        [customer.model_dump()],
        columns=[
            "tenure_months",
            "monthly_charges",
            "support_calls",
            "contract",
            "internet_service",
        ],
    )
    probability = float(model.predict_proba(features)[0, 1])
    return {
        "churn_probability": round(probability, 3),
        "predicted_churn": int(probability >= 0.5),
    }

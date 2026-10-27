"""Train the Lab 1 churn model and save it for the API."""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NUMERIC = ["tenure_months", "monthly_charges", "support_calls"]
CATEGORICAL = ["contract", "internet_service"]
FEATURES = NUMERIC + CATEGORICAL


def train(data_path: Path, model_path: Path) -> tuple[float, float]:
    """Fit a reproducible pipeline, report metrics, and save the whole pipeline."""
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    df = pd.read_csv(data_path)
    # Lab 1 Twist 1 renamed this field in churn_v2.csv. Normalize it here so
    # the model/API keep the same input contract for either dataset version.
    if "monthly_charges" not in df.columns and "monthly_fee" in df.columns:
        df = df.rename(columns={"monthly_fee": "monthly_charges"})

    required = set(FEATURES + ["churn"])
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    X = df[FEATURES]
    y = df["churn"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = Pipeline(
        steps=[
            (
                "prep",
                ColumnTransformer(
                    transformers=[
                        ("num", StandardScaler(), NUMERIC),
                        (
                            "cat",
                            OneHotEncoder(handle_unknown="ignore"),
                            CATEGORICAL,
                        ),
                    ]
                ),
            ),
            ("clf", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    model.fit(X_train, y_train)
    probabilities = model.predict_proba(X_test)[:, 1]
    f1 = float(f1_score(y_test, probabilities >= 0.5))
    auc = float(roc_auc_score(y_test, probabilities))

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    print(f"Dataset: {data_path.name}")
    print(f"F1: {f1:.3f}")
    print(f"AUC: {auc:.3f}")
    print(f"Saved model to: {model_path}")
    return f1, auc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=PROJECT_ROOT / "data" / "churn_v1.csv",
        help="CSV file to train from (v1 or v2)",
    )
    parser.add_argument(
        "--model-out",
        type=Path,
        default=PROJECT_ROOT / "model.joblib",
        help="Where to save the trained model",
    )
    args = parser.parse_args()
    train(args.data.resolve(), args.model_out.resolve())


if __name__ == "__main__":
    main()

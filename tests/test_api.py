"""The five-plus required behavioral checks for the churn API."""
from fastapi.testclient import TestClient

from src.app.main import app, load_model

client = TestClient(app)
VALID_CUSTOMER = {
    "tenure_months": 12,
    "monthly_charges": 70.5,
    "support_calls": 2,
    "contract": "month-to-month",
    "internet_service": "fiber",
}


def test_model_loads():
    model = load_model()
    assert hasattr(model, "predict_proba")


def test_health_endpoint_confirms_model_is_ready():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_returns_api_contract():
    response = client.post("/predict", json=VALID_CUSTOMER)
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"churn_probability", "predicted_churn"}
    assert 0.0 <= body["churn_probability"] <= 1.0
    assert body["predicted_churn"] in (0, 1)


def test_input_schema_rejects_missing_and_unknown_fields():
    missing_field = dict(VALID_CUSTOMER)
    del missing_field["contract"]
    assert client.post("/predict", json=missing_field).status_code == 422

    unknown_field = {**VALID_CUSTOMER, "customer_id": "not-an-api-feature"}
    assert client.post("/predict", json=unknown_field).status_code == 422


def test_edge_case_rejects_negative_months_and_unknown_category():
    negative_months = {**VALID_CUSTOMER, "tenure_months": -1}
    assert client.post("/predict", json=negative_months).status_code == 422

    invalid_contract = {**VALID_CUSTOMER, "contract": "forever"}
    assert client.post("/predict", json=invalid_contract).status_code == 422


def test_prediction_is_deterministic_for_same_input():
    first = client.post("/predict", json=VALID_CUSTOMER).json()
    second = client.post("/predict", json=VALID_CUSTOMER).json()
    assert first == second

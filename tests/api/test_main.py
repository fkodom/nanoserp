from fastapi.testclient import TestClient

from {{REPO_NAME_SNAKECASE}}.api.main import HealthResponse, app


def test_import_app():
    # Dumbest possible test, to check that the app can be imported without crashing
    assert app is not None


def test_is_healthy(mock_app: TestClient):
    response = mock_app.get("/health")
    response.raise_for_status()
    response_model = HealthResponse(**response.json())
    assert response_model.status == "ok"

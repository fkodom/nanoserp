from fastapi.testclient import TestClient

from {{REPO_NAME_SNAKECASE}}.settings import AuthSettings


def test_example_crud(mock_app: TestClient):
    api_key = AuthSettings().API_KEY
    headers = {"Authorization": f"Bearer {api_key}"}
    response = mock_app.post(
        "/api/v1/examples", json={"data": "This is an example."}, headers=headers
    )
    response.raise_for_status()

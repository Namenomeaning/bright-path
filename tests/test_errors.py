from fastapi.testclient import TestClient

from app.main import create_app


def test_unknown_path_uses_the_error_format():
    client = TestClient(create_app())

    response = client.get("/nope")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Not Found"}}

from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from dentxplain.service.app import app


def test_health_and_web_app() -> None:
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    assert "DentXplain" in client.get("/").text


def test_predict_rejects_non_image_content_type() -> None:
    response = TestClient(app).post(
        "/v1/predict", content=b"not an image", headers={"content-type": "text/plain"}
    )
    assert response.status_code == 415


def test_predict_accepts_file_upload(monkeypatch) -> None:
    class FakePipeline:
        def predict(self, image: Image.Image, image_id: str | None = None) -> dict:
            return {"image_id": image_id, "size": image.size}

    monkeypatch.setattr("dentxplain.service.app.get_pipeline", lambda: FakePipeline())
    stream = BytesIO()
    Image.new("RGB", (8, 6)).save(stream, format="PNG")
    response = TestClient(app).post(
        "/v1/predict",
        files={"file": ("sample.png", stream.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    assert response.json() == {"image_id": "sample.png", "size": [8, 6]}

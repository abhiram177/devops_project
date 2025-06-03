# test_app.py

import os
import pytest
import importlib
from flask import json

# We won’t import `app` at the top level. Instead, we’ll import it inside fixtures
# so that changes to the environment take effect before `app.py` runs.

@pytest.fixture
def client(monkeypatch):
    # 1. Ensure GOOGLE_API_KEY is unset so we hit the mocked branch.
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    # 2. Reload the app module so it re-reads the (now-empty) env var.
    #    If it was already imported in a previous test, this forces re-import.
    import app
    importlib.reload(app)
    
    # 3. Grab the fresh Flask app instance and create a test client.
    flask_client = app.app.test_client()
    yield flask_client

def test_no_question(client):
    # Missing "question" should return 400
    response = client.post("/ask", data="{}", content_type="application/json")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"] == "No question provided"

def test_mocked_response(client):
    # With no GOOGLE_API_KEY set, we should get a mocked answer
    payload = {"question": "How are you?"}
    response = client.post(
        "/ask",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["answer"].startswith("[mocked answer]")

@pytest.fixture
def real_key_client(monkeypatch):
    # 1. Set a fake GOOGLE_API_KEY so `app.py` initializes a real client
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")

    # 2. Monkey-patch genai.Client before loading/reloading `app.py`.
    #    We hijack the constructor to return a dummy client
    from types import SimpleNamespace

    class DummyResponse(SimpleNamespace):
        text = "Dummy real response"

    class DummyModel:
        def generate_content(self, model, contents, config):
            return DummyResponse()

    class DummyClient:
        models = DummyModel()

    # Patch the Client in the google.genai namespace
    monkeypatch.setattr("google.genai.Client", lambda api_key: DummyClient())

    # 3. Reload `app.py` so it picks up our fake key & patched Client
    import app
    importlib.reload(app)

    # 4. Create and yield the test client
    flask_client = app.app.test_client()
    yield flask_client

def test_real_branch(real_key_client):
    payload = {"question": "Tell me a joke"}
    response = real_key_client.post(
        "/ask",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["answer"] == "Dummy real response"

import re

import pytest

import app as app_module
from app import Message, app, db


@pytest.fixture
def client():
    app.config.update(TESTING=True)
    app_module._contact_attempts.clear()
    with app.app_context():
        db.session.execute(db.delete(Message))
        db.session.commit()
    with app.test_client() as client:
        yield client


def saved_messages():
    with app.app_context():
        return db.session.execute(db.select(Message)).scalars().all()


def csrf_token(client):
    html = client.get("/contact").get_data(as_text=True)
    return re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html).group(1)


def valid_form(client, **overrides):
    data = {
        "csrf_token": csrf_token(client),
        "name": "Jane Smith",
        "email": "jane@example.com",
        "project_type": "mobile",
        "message": "I'd like an iPhone app for my bakery.",
        "website": "",
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize("path, text", [
    ("/", "Ideas"),
    ("/work", "Selected"),
    ("/about", "Joshua."),
    ("/contact", "Send message"),
])
def test_pages_load(client, path, text):
    response = client.get(path)
    assert response.status_code == 200
    assert text in response.get_data(as_text=True)


def test_security_headers(client):
    headers = client.get("/").headers
    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"


def test_missing_page_returns_404(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert "doesn't exist" in response.get_data(as_text=True)


def test_contact_form_saves_message(client):
    response = client.post("/contact", data=valid_form(client), follow_redirects=True)
    assert "Message sent." in response.get_data(as_text=True)

    [saved] = saved_messages()
    assert saved.email == "jane@example.com"
    assert saved.project_type == "Mobile app"


def test_contact_form_rejects_missing_csrf_token(client):
    data = valid_form(client)
    del data["csrf_token"]
    response = client.post("/contact", data=data)
    assert "Message sent." not in response.get_data(as_text=True)
    assert saved_messages() == []


def test_contact_form_shows_validation_errors(client):
    response = client.post("/contact", data=valid_form(client, email="not-an-email", message="hi"))
    html = response.get_data(as_text=True)
    assert "doesn&#39;t look right" in html
    assert "between 10 and 5,000" in html
    assert saved_messages() == []


def test_contact_form_ignores_honeypot_submissions(client):
    response = client.post("/contact", data=valid_form(client, website="http://spam.example"), follow_redirects=True)
    assert "Message sent." in response.get_data(as_text=True)
    assert saved_messages() == []


def test_contact_form_rate_limit(client):
    for _ in range(app_module.CONTACT_LIMIT):
        client.post("/contact", data=valid_form(client))
    response = client.post("/contact", data=valid_form(client), follow_redirects=True)
    assert "try again later" in response.get_data(as_text=True)


def test_user_input_is_escaped(client):
    response = client.post("/contact", data=valid_form(client, email="<script>alert(1)</script>"))
    html = response.get_data(as_text=True)
    assert "<script>alert(1)</script>" not in html


def test_sql_injection_attempt_is_stored_as_plain_text(client):
    attack = "Robert'); DROP TABLE message;--"
    client.post("/contact", data=valid_form(client, name=attack))
    [saved] = saved_messages()
    assert saved.name == attack  # stored safely as text; the table still exists


def test_database_url_uses_psycopg_driver(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@host/db")
    assert app_module.database_url() == "postgresql+psycopg://user:pw@host/db"

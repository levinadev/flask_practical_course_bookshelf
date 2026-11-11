import pytest
from flask import g, session

from bookshelf.db import get_db


def test_register(client, app):
    assert client.get("/auth/register").status_code == 200
    response = client.post("/auth/register", data={"username": "olga", "password": "qwerty1"})
    assert response.headers["Location"] == "/auth/login"
    with app.app_context():
        user = get_db().execute("SELECT * FROM user WHERE username = 'olga'").fetchone()
        assert user is not None
        assert user["password"] != "qwerty1"


@pytest.mark.parametrize(("username", "password", "message"), (
    ("", "qwerty1", "Введите имя пользователя."),
    ("olga", "123", "Пароль должен быть не короче 6 символов."),
    ("anna", "qwerty1", "уже зарегистрирован"),
))
def test_register_validation(client, username, password, message):
    response = client.post("/auth/register", data={"username": username, "password": password})
    assert message in response.get_data(as_text=True)


def test_login(client, auth):
    assert client.get("/auth/login").status_code == 200
    response = auth.login()
    assert response.headers["Location"] == "/"
    with client:
        client.get("/")
        assert session["user_id"] == 1
        assert g.user["username"] == "anna"


@pytest.mark.parametrize(("username", "password"), (("nobody", "secret1"), ("anna", "wrong")))
def test_login_validation(auth, username, password):
    response = auth.login(username, password)
    assert "Неверное имя пользователя или пароль." in response.get_data(as_text=True)


def test_logout(client, auth):
    auth.login()
    with client:
        auth.logout()
        assert "user_id" not in session

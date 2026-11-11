import os
import tempfile

import pytest
from werkzeug.security import generate_password_hash

from bookshelf import create_app
from bookshelf.db import get_db, init_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"TESTING": True, "DATABASE": db_path, "SECRET_KEY": "test"})

    with app.app_context():
        init_db()
        db = get_db()
        db.executemany("INSERT INTO user (username, password) VALUES (?, ?)", [
            ("anna", generate_password_hash("secret1")),
            ("ivan", generate_password_hash("secret2")),
        ])
        db.executemany("INSERT INTO book (user_id, title, author, status, rating) VALUES (?, ?, ?, ?, ?)", [
            (1, "Мастер и Маргарита", "Булгаков", "done", 5),
            (1, "Дюна", "Герберт", "reading", None),
            (2, "Идиот", "Достоевский", "want", None),
        ])
        db.commit()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, username="anna", password="secret1"):
        return self._client.post("/auth/login", data={"username": username, "password": password})

    def logout(self):
        return self._client.get("/auth/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)

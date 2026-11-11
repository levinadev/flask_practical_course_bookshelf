import pytest

from bookshelf.db import get_db


@pytest.mark.parametrize("path", ("/", "/books/new", "/books/1/edit", "/stats"))
def test_login_required(client, path):
    response = client.get(path)
    assert response.headers["Location"] == "/auth/login"


def test_index_shows_only_own_books(client, auth):
    auth.login()
    html = client.get("/").get_data(as_text=True)
    assert "Мастер и Маргарита" in html
    assert "Дюна" in html
    assert "Идиот" not in html


def test_filter_by_status(client, auth):
    auth.login()
    html = client.get("/?status=done").get_data(as_text=True)
    assert "Мастер и Маргарита" in html
    assert "Дюна" not in html


def test_create(client, auth, app):
    auth.login()
    response = client.post("/books/new", data={"title": "Солярис", "author": "Лем", "status": "want", "rating": ""})
    assert response.headers["Location"] == "/"
    with app.app_context():
        count = get_db().execute("SELECT COUNT(*) FROM book WHERE user_id = 1").fetchone()[0]
        assert count == 3


@pytest.mark.parametrize(("data", "message"), (
    ({"title": "", "author": "Лем"}, "Укажите название книги."),
    ({"title": "Солярис", "author": ""}, "Укажите автора."),
    ({"title": "Солярис", "author": "Лем", "rating": "7"}, "Оценка должна быть от 1 до 5."),
))
def test_create_validation(client, auth, data, message):
    auth.login()
    response = client.post("/books/new", data=data)
    assert message in response.get_data(as_text=True)


def test_update(client, auth, app):
    auth.login()
    client.post("/books/2/edit", data={"title": "Дюна", "author": "Фрэнк Герберт", "status": "done", "rating": "4"})
    with app.app_context():
        book = get_db().execute("SELECT * FROM book WHERE id = 2").fetchone()
        assert book["author"] == "Фрэнк Герберт"
        assert book["rating"] == 4


def test_other_users_book_is_forbidden(client, auth):
    auth.login()
    assert client.get("/books/3/edit").status_code == 403
    assert client.post("/books/3/delete").status_code == 403
    assert client.get("/books/99/edit").status_code == 404


def test_delete(client, auth, app):
    auth.login()
    response = client.post("/books/1/delete")
    assert response.headers["Location"] == "/"
    with app.app_context():
        assert get_db().execute("SELECT * FROM book WHERE id = 1").fetchone() is None


def test_stats(client, auth):
    auth.login()
    html = client.get("/stats").get_data(as_text=True)
    assert "всего книг" in html

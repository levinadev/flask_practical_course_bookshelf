def test_requires_login(client):
    response = client.get("/api/books")
    assert response.status_code == 401
    assert response.get_json() == {"error": "Требуется вход"}


def test_list_books(client, auth):
    auth.login()
    books = client.get("/api/books").get_json()
    assert [b["title"] for b in books] == ["Мастер и Маргарита", "Дюна"]


def test_get_book(client, auth):
    auth.login()
    assert client.get("/api/books/1").get_json()["author"] == "Булгаков"
    assert client.get("/api/books/3").status_code == 403
    assert client.get("/api/books/99").get_json() == {"error": "Не найдено"}


def test_create_book(client, auth):
    auth.login()
    response = client.post("/api/books", json={"title": "Солярис", "author": "Лем", "rating": 5})
    assert response.status_code == 201
    assert response.get_json() == {"id": 4, "title": "Солярис", "author": "Лем", "status": "want", "rating": 5, "note": ""}


def test_create_book_validation(client, auth):
    auth.login()
    assert client.post("/api/books", json={"title": "Без автора"}).status_code == 400
    assert client.post("/api/books", json={"title": "А", "author": "Б", "status": "lost"}).status_code == 400
    assert client.post("/api/books", json={"title": "А", "author": "Б", "rating": 10}).status_code == 400
    assert client.post("/api/books", data="не json").status_code == 400


def test_stats(client, auth):
    auth.login()
    assert client.get("/api/stats").get_json() == {"total": 2, "want": 0, "reading": 1, "done": 1}

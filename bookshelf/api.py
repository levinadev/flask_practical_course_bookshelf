from flask import Blueprint, g, request

from .books import STATUSES, get_book
from .db import get_db

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.before_request
def require_login():
    if g.user is None:
        return {"error": "Требуется вход"}, 401


@bp.errorhandler(403)
def forbidden(error):
    return {"error": "Доступ запрещён"}, 403


@bp.errorhandler(404)
def not_found(error):
    return {"error": "Не найдено"}, 404


def to_dict(row):
    return {key: row[key] for key in ("id", "title", "author", "status", "rating", "note")}


@bp.get("/books")
def list_books():
    rows = get_db().execute("SELECT * FROM book WHERE user_id = ? ORDER BY id", (g.user["id"],)).fetchall()
    return [to_dict(row) for row in rows]


@bp.get("/books/<int:book_id>")
def get_one(book_id):
    return to_dict(get_book(book_id))


@bp.post("/books")
def create_book():
    data = request.get_json(silent=True) or {}
    title, author = data.get("title"), data.get("author")
    status, rating = data.get("status", "want"), data.get("rating")
    if not isinstance(title, str) or not title.strip() or not isinstance(author, str) or not author.strip():
        return {"error": "Поля title и author обязательны"}, 400
    if status not in STATUSES:
        return {"error": "Неизвестный статус"}, 400
    if rating is not None and (not isinstance(rating, int) or not 1 <= rating <= 5):
        return {"error": "Оценка должна быть от 1 до 5"}, 400
    db = get_db()
    cursor = db.execute(
        "INSERT INTO book (user_id, title, author, status, rating) VALUES (?, ?, ?, ?, ?)",
        (g.user["id"], title.strip(), author.strip(), status, rating),
    )
    db.commit()
    return to_dict(get_book(cursor.lastrowid)), 201


@bp.get("/stats")
def stats():
    rows = get_db().execute("SELECT status, COUNT(*) AS n FROM book WHERE user_id = ? GROUP BY status", (g.user["id"],))
    counts = {key: 0 for key in STATUSES}
    counts.update({row["status"]: row["n"] for row in rows})
    return {"total": sum(counts.values()), **counts}

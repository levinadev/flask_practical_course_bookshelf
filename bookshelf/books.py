from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .auth import login_required
from .db import get_db

bp = Blueprint("books", __name__)

STATUSES = {"want": "Хочу прочитать", "reading": "Читаю", "done": "Прочитано"}


def get_book(book_id, check_owner=True):
    """Книга по id; 404, если её нет, 403, если она чужая."""
    book = get_db().execute("SELECT * FROM book WHERE id = ?", (book_id,)).fetchone()
    if book is None:
        abort(404)
    if check_owner and book["user_id"] != g.user["id"]:
        abort(403)
    return book


def read_form():
    """Данные формы книги и список ошибок."""
    data = {
        "title": request.form.get("title", "").strip(),
        "author": request.form.get("author", "").strip(),
        "status": request.form.get("status", "want"),
        "rating": request.form.get("rating", type=int),
        "note": request.form.get("note", "").strip(),
    }
    errors = []
    if not data["title"]:
        errors.append("Укажите название книги.")
    if not data["author"]:
        errors.append("Укажите автора.")
    if data["status"] not in STATUSES:
        errors.append("Неизвестный статус.")
    if data["rating"] is not None and not 1 <= data["rating"] <= 5:
        errors.append("Оценка должна быть от 1 до 5.")
    return data, errors


@bp.route("/")
@login_required
def index():
    status = request.args.get("status")
    query = "SELECT * FROM book WHERE user_id = ?"
    params = [g.user["id"]]
    if status in STATUSES:
        query += " AND status = ?"
        params.append(status)
    books = get_db().execute(query + " ORDER BY created DESC, id DESC", params).fetchall()
    return render_template("books/index.html", books=books, statuses=STATUSES, current_status=status)


@bp.route("/books/new", methods=("GET", "POST"))
@login_required
def create():
    if request.method == "POST":
        data, errors = read_form()
        if not errors:
            db = get_db()
            db.execute(
                "INSERT INTO book (user_id, title, author, status, rating, note) VALUES (?, ?, ?, ?, ?, ?)",
                (g.user["id"], data["title"], data["author"], data["status"], data["rating"], data["note"]),
            )
            db.commit()
            flash("Книга добавлена на полку.", "success")
            return redirect(url_for("index"))
        for error in errors:
            flash(error, "error")
    return render_template("books/form.html", book=None, statuses=STATUSES)


@bp.route("/books/<int:book_id>/edit", methods=("GET", "POST"))
@login_required
def update(book_id):
    book = get_book(book_id)
    if request.method == "POST":
        data, errors = read_form()
        if not errors:
            db = get_db()
            db.execute(
                "UPDATE book SET title = ?, author = ?, status = ?, rating = ?, note = ? WHERE id = ?",
                (data["title"], data["author"], data["status"], data["rating"], data["note"], book_id),
            )
            db.commit()
            flash("Изменения сохранены.", "success")
            return redirect(url_for("index"))
        for error in errors:
            flash(error, "error")
    return render_template("books/form.html", book=book, statuses=STATUSES)


@bp.post("/books/<int:book_id>/delete")
@login_required
def delete(book_id):
    get_book(book_id)
    db = get_db()
    db.execute("DELETE FROM book WHERE id = ?", (book_id,))
    db.commit()
    flash("Книга удалена.", "success")
    return redirect(url_for("index"))


@bp.route("/stats")
@login_required
def stats():
    db = get_db()
    counts = {key: 0 for key in STATUSES}
    for row in db.execute("SELECT status, COUNT(*) AS n FROM book WHERE user_id = ? GROUP BY status", (g.user["id"],)):
        counts[row["status"]] = row["n"]
    avg = db.execute("SELECT AVG(rating) FROM book WHERE user_id = ? AND rating IS NOT NULL", (g.user["id"],)).fetchone()[0]
    return render_template("books/stats.html", counts=counts, statuses=STATUSES,
                           total=sum(counts.values()), avg_rating=round(avg, 1) if avg else None)

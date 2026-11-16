import os

from flask import Flask, render_template


def create_app(test_config=None):
    """Фабрика приложения "Книжная полка"."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        DATABASE=os.path.join(app.instance_path, "bookshelf.sqlite"),
    )

    if test_config is None:
        # настройки рабочего сервера: instance/config.py (не храним в репозитории)
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    from . import db
    db.init_app(app)

    from . import auth, books, api
    app.register_blueprint(auth.bp)
    app.register_blueprint(books.bp)
    app.register_blueprint(api.bp)
    app.add_url_rule("/", endpoint="index")
    app.json.ensure_ascii = False

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/error.html", code=403, message="Доступ запрещён"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/error.html", code=404, message="Страница не найдена"), 404

    return app

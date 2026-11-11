from bookshelf import create_app


def test_config():
    assert not create_app().testing
    assert create_app({"TESTING": True}).testing


def test_init_db_command(runner, monkeypatch):
    called = []
    monkeypatch.setattr("bookshelf.db.init_db", lambda: called.append(True))
    result = runner.invoke(args=["init-db"])
    assert "База данных создана" in result.output
    assert called

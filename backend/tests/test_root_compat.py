def test_app_backend_main_imports_backend_app():
    import app.backend.main as compat
    import app.main as backend_app

    assert compat.app is not None
    assert compat.health_check is not None
    assert backend_app.app is not None
    assert backend_app.health_check is not None

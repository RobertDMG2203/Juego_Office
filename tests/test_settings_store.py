from __future__ import annotations

import config
from settings_store import TeacherSettings


def test_teacher_settings_level_and_password(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    settings = TeacherSettings()
    assert settings.verify_password(config.CONTRASENA_PROFESOR)
    settings.set_education_level("preparatoria")
    assert settings.get_education_level() == "preparatoria"
    ok, _ = settings.change_password(config.CONTRASENA_PROFESOR, "ClaveNueva2026!")
    assert ok
    assert settings.verify_password("ClaveNueva2026!")
    assert not settings.verify_password(config.CONTRASENA_PROFESOR)


def test_teacher_can_toggle_hints(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    settings = TeacherSettings()
    assert settings.get_show_hints() is True
    settings.set_show_hints(False)
    assert settings.get_show_hints() is False
    settings.set_show_hints(True)
    assert settings.get_show_hints() is True

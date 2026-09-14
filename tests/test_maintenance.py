from __future__ import annotations

import csv
import json
from datetime import datetime

from maintenance import clean_cache, purge_records, reset_cycle_data


def _write_summary(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["nombre", "matricula", "grupo", "inicio", "fin", "calificacion", "precision"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _write_log(path, stamp):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"timestamp": stamp, "event": "session_start"}) + "\n", encoding="utf-8")


def test_purge_old_records_and_reset_cycle(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    logs = tmp_path / "MisionDigital" / "logs"
    summary = logs / "resumen_sesiones.csv"
    _write_summary(summary, [
        {"nombre": "Viejo", "matricula": "1", "grupo": "A", "inicio": "2025-01-01T10:00:00", "fin": "2025-01-01T11:00:00", "calificacion": "80", "precision": "80"},
        {"nombre": "Nuevo", "matricula": "2", "grupo": "A", "inicio": "2026-08-20T10:00:00", "fin": "2026-08-20T11:00:00", "calificacion": "90", "precision": "90"},
    ])
    _write_log(logs / "1_old.jsonl", "2025-01-01T10:00:00")
    _write_log(logs / "2_new.jsonl", "2026-08-20T10:00:00")

    result = purge_records(180, now=datetime(2026, 9, 14, 12, 0, 0))
    assert result["rows_deleted"] == 1
    assert result["files_deleted"] == 1
    text = summary.read_text(encoding="utf-8-sig")
    assert "Nuevo" in text and "Viejo" not in text
    assert (logs / "2_new.jsonl").exists()

    progress = tmp_path / "MisionDigital" / "progreso" / "2.json"
    progress.parent.mkdir(parents=True, exist_ok=True)
    progress.write_text("{}", encoding="utf-8")
    settings = tmp_path / "MisionDigital" / "configuracion_profesor.json"
    settings.write_text("{}", encoding="utf-8")
    reset_cycle_data()
    assert not logs.exists()
    assert not progress.parent.exists()
    assert settings.exists()


def test_clean_cache_keeps_records(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    root = tmp_path / "MisionDigital"
    cache = root / "cache"
    cache.mkdir(parents=True)
    (cache / "temp.bin").write_bytes(b"abc")
    logs = root / "logs"
    logs.mkdir()
    (logs / "keep.jsonl").write_text("{}\n", encoding="utf-8")
    (root / "orphan.tmp").write_text("tmp", encoding="utf-8")

    result = clean_cache()
    assert result["items"] >= 2
    assert (logs / "keep.jsonl").exists()
    assert cache.exists()
    assert not (root / "orphan.tmp").exists()


def test_uninstall_preserves_python_and_source(tmp_path, monkeypatch):
    """La desinstalación jamás debe incluir pip, site-packages ni el repo de desarrollo."""
    from pathlib import Path
    from maintenance import schedule_uninstall

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    result = schedule_uninstall(remove_source_code=True)
    script = Path(result["script"])
    text = script.read_text(encoding="utf-8").lower()

    assert result["python_preserved"] is True
    assert result["source_preserved"] is True
    assert result["source_root"] == ""
    assert "pip uninstall" not in text
    assert "site-packages" not in text
    assert ".mision_digital_venv" not in text
    assert "python.exe" not in text

    from maintenance import _build_uninstall_powershell
    ps = _build_uninstall_powershell(1234, None, (tmp_path / "MisionDigital").resolve(), tmp_path / "u.log").lower()
    assert str((tmp_path / "MisionDigital").resolve()).lower() in ps


def test_uninstall_waits_for_exe_and_retries(tmp_path, monkeypatch):
    """El helper debe esperar al PID y reintentar el borrado del EXE bloqueado."""
    import sys
    from pathlib import Path
    from maintenance import schedule_uninstall, _build_uninstall_powershell

    fake_exe = tmp_path / "Escritorio Alumno" / "MisionDigital.exe"
    fake_exe.parent.mkdir(parents=True)
    fake_exe.write_bytes(b"fake")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    result = schedule_uninstall(remove_source_code=False)
    text = Path(result["script"]).read_text(encoding="ascii").lower()

    assert result["frozen"] is True
    assert "-encodedcommand" in text
    assert "pip uninstall" not in text
    assert "site-packages" not in text

    ps = _build_uninstall_powershell(1234, fake_exe.resolve(), tmp_path / "LocalAppData" / "MisionDigital", tmp_path / "u.log").lower()
    assert str(fake_exe.resolve()).lower() in ps
    assert "wait-process -id $pidtowait" in ps
    assert "$i -le 60" in ps
    assert "remove-item -literalpath $targetexe" in ps


def test_uninstall_launcher_is_ascii_even_with_unicode_paths(tmp_path, monkeypatch):
    """Las rutas con acentos deben viajar dentro de EncodedCommand, no romper el BAT."""
    import sys
    from pathlib import Path
    from maintenance import schedule_uninstall

    fake_exe = tmp_path / "José Álvarez" / "Escritorio" / "MisionDigital.exe"
    fake_exe.parent.mkdir(parents=True)
    fake_exe.write_bytes(b"fake")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Datos José"))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(fake_exe))

    result = schedule_uninstall()
    raw = Path(result["script"]).read_bytes()
    raw.decode("ascii")  # No debe lanzar UnicodeDecodeError.
    assert b"-EncodedCommand" in raw

from __future__ import annotations

import base64
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path


def app_data_dir() -> Path:
    """Directorio privado de datos de Misión Digital en el perfil de Windows."""
    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "MisionDigital"


def cache_dir() -> Path:
    return app_data_dir() / "cache"


def hidden_source_dir() -> Path:
    """Ubicación opcional creada por guardar_codigo_oculto.bat."""
    return app_data_dir() / "codigo_fuente"


def _remove_path(path: Path) -> int:
    """Elimina path y devuelve una aproximación de bytes liberados."""
    if not path.exists():
        return 0
    size = 0
    try:
        if path.is_file() or path.is_symlink():
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            path.unlink(missing_ok=True)
            return size
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    size += item.stat().st_size
                except OSError:
                    pass
        shutil.rmtree(path, ignore_errors=False)
        return size
    except OSError:
        return size


def clean_cache(project_root: Path | None = None) -> dict:
    """Limpia únicamente temporales/caché de la aplicación.

    Nunca borra resultados, progresos ni la configuración del profesor.
    En modo código también elimina __pycache__ del propio proyecto.
    """
    removed_items = 0
    freed_bytes = 0
    root = app_data_dir()

    target = cache_dir()
    if target.exists():
        freed_bytes += _remove_path(target)
        removed_items += 1

    if root.exists():
        for temp_file in root.rglob("*.tmp"):
            try:
                freed_bytes += temp_file.stat().st_size
            except OSError:
                pass
            try:
                temp_file.unlink()
                removed_items += 1
            except OSError:
                pass

    if project_root:
        project_root = Path(project_root).resolve()
        # Sólo se tocan cachés de Python dentro del proyecto suministrado.
        for pycache in list(project_root.rglob("__pycache__")):
            if pycache.is_dir():
                try:
                    freed_bytes += _remove_path(pycache)
                    removed_items += 1
                except OSError:
                    pass

    cache_dir().mkdir(parents=True, exist_ok=True)
    return {"items": removed_items, "bytes": freed_bytes}


def _parse_date(row: dict) -> datetime | None:
    for key in ("inicio", "fin"):
        value = str(row.get(key, "") or "").strip()
        if not value:
            continue
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return None


def _jsonl_date(path: Path) -> datetime | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            first = handle.readline().strip()
        if not first:
            return None
        record = json.loads(first)
        stamp = str(record.get("timestamp", ""))
        return datetime.fromisoformat(stamp) if stamp else None
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def purge_records(older_than_days: int | None, now: datetime | None = None) -> dict:
    """Elimina resultados antiguos locales e importados y sus logs detallados.

    older_than_days=None significa eliminar todos los resultados históricos.
    Los progresos por matrícula se conservan; para fin de ciclo use reset_cycle_data().
    Filas con fecha ilegible se conservan en borrados por antigüedad para evitar pérdida accidental.
    """
    if older_than_days is not None and older_than_days < 1:
        raise ValueError("older_than_days debe ser >= 1 o None")

    now = now or datetime.now()
    cutoff = None if older_than_days is None else now - timedelta(days=older_than_days)
    root = app_data_dir()
    log_dir = root / "logs"
    summary_paths = [log_dir / "resumen_sesiones.csv", root / "importados" / "resumen_importado.csv"]
    rows_deleted = 0
    files_deleted = 0

    for summary_path in summary_paths:
        if not summary_path.exists():
            continue
        try:
            with summary_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                fieldnames = list(reader.fieldnames or [])
        except OSError:
            rows, fieldnames = [], []

        keep: list[dict] = []
        deleted_here = 0
        for row in rows:
            row_date = _parse_date(row)
            should_delete = cutoff is None or (row_date is not None and row_date < cutoff)
            if should_delete:
                rows_deleted += 1
                deleted_here += 1
            else:
                keep.append(row)

        try:
            if keep and fieldnames:
                temp = summary_path.with_suffix(".tmp")
                with temp.open("w", encoding="utf-8-sig", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(keep)
                temp.replace(summary_path)
            elif deleted_here:
                summary_path.unlink(missing_ok=True)
        except OSError:
            pass

    detail_dirs = [log_dir, root / "importados" / "detalle"]
    for detail_dir in detail_dirs:
        if not detail_dir.exists():
            continue
        for path in detail_dir.glob("*.jsonl"):
            stamp = _jsonl_date(path)
            should_delete = cutoff is None or (stamp is not None and stamp < cutoff)
            if should_delete:
                try:
                    path.unlink()
                    files_deleted += 1
                except OSError:
                    pass

    return {"rows_deleted": rows_deleted, "files_deleted": files_deleted}


def reset_cycle_data() -> dict:
    """Borra resultados y progresos del alumnado, conservando configuración docente."""
    root = app_data_dir()
    removed = []
    freed = 0
    for name in ("logs", "progreso", "cache", "importados"):
        target = root / name
        if target.exists():
            try:
                freed += _remove_path(target)
                removed.append(name)
            except OSError:
                pass
    cache_dir().mkdir(parents=True, exist_ok=True)
    return {"removed": removed, "bytes": freed}


def _ps_literal(value: str) -> str:
    '''Escapa un valor como literal de PowerShell entre comillas simples.'''
    return "'" + str(value).replace("'", "''") + "'"


def _build_uninstall_powershell(
    current_pid: int,
    executable: Path | None,
    data_root: Path,
    log_file: Path,
) -> str:
    '''Construye el helper externo que espera al proceso y elimina sus archivos.'''
    target = _ps_literal(str(executable)) if executable else "$null"
    data = _ps_literal(str(data_root))
    log = _ps_literal(str(log_file))
    return f"""$ErrorActionPreference = 'SilentlyContinue'
$pidToWait = {int(current_pid)}
$targetExe = {target}
$dataRoot = {data}
$logFile = {log}
Set-Content -LiteralPath $logFile -Value 'MISION DIGITAL - DESINSTALACION' -Encoding UTF8
Add-Content -LiteralPath $logFile -Value ('Esperando al proceso PID ' + $pidToWait + '...') -Encoding UTF8
try {{ Wait-Process -Id $pidToWait -ErrorAction SilentlyContinue }} catch {{}}
if ($null -ne $targetExe) {{
    $deleted = $false
    for ($i = 1; $i -le 60; $i++) {{
        if (-not (Test-Path -LiteralPath $targetExe)) {{ $deleted = $true; break }}
        Remove-Item -LiteralPath $targetExe -Force -ErrorAction SilentlyContinue
        if (-not (Test-Path -LiteralPath $targetExe)) {{ $deleted = $true; break }}
        Start-Sleep -Seconds 1
    }}
    if ($deleted) {{
        Add-Content -LiteralPath $logFile -Value ('Ejecutable eliminado: ' + $targetExe) -Encoding UTF8
    }} else {{
        Add-Content -LiteralPath $logFile -Value ('ERROR: no se pudo eliminar el ejecutable tras 60 intentos: ' + $targetExe) -Encoding UTF8
    }}
}}
if (Test-Path -LiteralPath $dataRoot) {{
    Remove-Item -LiteralPath $dataRoot -Recurse -Force -ErrorAction SilentlyContinue
}}
if (Test-Path -LiteralPath $dataRoot) {{
    Add-Content -LiteralPath $logFile -Value ('ADVERTENCIA: quedaron datos locales en ' + $dataRoot) -Encoding UTF8
}} else {{
    Add-Content -LiteralPath $logFile -Value 'Datos locales eliminados.' -Encoding UTF8
}}
Add-Content -LiteralPath $logFile -Value 'Fin de desinstalacion.' -Encoding UTF8
"""


def schedule_uninstall(remove_source_code: bool = True) -> dict:
    '''Programa una desinstalación segura y verificable en Windows.

    La aplicación compilada no intenta borrarse a sí misma. Se lanza un helper
    externo en PowerShell mediante -EncodedCommand. El helper espera al PID exacto
    y después reintenta el borrado del EXE hasta 60 veces.

    Las rutas viajan codificadas en UTF-16LE/base64, por lo que nombres de usuario
    con acentos o caracteres Unicode no rompen el desinstalador. Nunca se ejecuta
    pip uninstall ni se toca Python, site-packages o entornos virtuales.
    '''
    del remove_source_code  # Se conserva por compatibilidad de API.

    data_root = app_data_dir().resolve()
    frozen = bool(getattr(sys, "frozen", False))
    executable = Path(sys.executable).resolve() if frozen else None
    current_pid = os.getpid()

    temp_dir = Path(tempfile.gettempdir())
    launcher = temp_dir / f"MisionDigital_desinstalar_{current_pid}.bat"
    log_file = temp_dir / "MisionDigital_desinstalacion.log"

    ps_script = _build_uninstall_powershell(current_pid, executable, data_root, log_file)
    encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")

    # El BAT contiene sólo ASCII + CRLF. Las rutas Unicode viajan dentro de
    # EncodedCommand y no dependen de la codificación de cmd.exe.
    launcher_lines = [
        "@echo off",
        "setlocal",
        "rem Mision Digital - helper externo de desinstalacion",
        f"powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -EncodedCommand {encoded}",
        "endlocal",
        'del /f /q "%~f0" >nul 2>&1',
    ]
    launcher.write_text("\r\n".join(launcher_lines) + "\r\n", encoding="ascii")

    if os.name == "nt":
        flags = (
            getattr(subprocess, "CREATE_NO_WINDOW", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )
        subprocess.Popen(
            ["cmd.exe", "/d", "/c", str(launcher)],
            creationflags=flags,
            close_fds=True,
        )
    else:
        return {
            "scheduled": False,
            "script": str(launcher),
            "log": str(log_file),
            "frozen": frozen,
            "executable": str(executable or ""),
            "source_root": "",
            "source_preserved": True,
            "python_preserved": True,
        }

    return {
        "scheduled": True,
        "script": str(launcher),
        "log": str(log_file),
        "frozen": frozen,
        "executable": str(executable or ""),
        "source_root": "",
        "source_preserved": True,
        "python_preserved": True,
    }

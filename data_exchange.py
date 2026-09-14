from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from maintenance import app_data_dir
from session_log import logs_dir

PACKAGE_VERSION = 1


def _safe(value: str) -> str:
    text = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(value).strip())
    return text[:60] or "sin_dato"


def desktop_dir() -> Path:
    """Devuelve una ubicación razonable del Escritorio en Windows y un fallback portable."""
    home = Path.home()
    candidates = []
    onedrive = os.environ.get("OneDrive") or os.environ.get("OneDriveCommercial")
    userprofile = os.environ.get("USERPROFILE")
    if onedrive:
        candidates.extend([Path(onedrive) / "Desktop", Path(onedrive) / "Escritorio"])
    if userprofile:
        candidates.extend([Path(userprofile) / "Desktop", Path(userprofile) / "Escritorio"])
    candidates.extend([home / "Desktop", home / "Escritorio"])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    fallback = candidates[0] if candidates else home / "Desktop"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def imported_dir() -> Path:
    path = app_data_dir() / "importados"
    path.mkdir(parents=True, exist_ok=True)
    return path


def imported_summary_path() -> Path:
    return imported_dir() / "resumen_importado.csv"


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except OSError:
        return []


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.unlink(missing_ok=True)
        return
    fields: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fields:
                fields.append(key)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)


def session_key(row: dict) -> str:
    identity = "|".join(
        str(row.get(key, "")).strip()
        for key in ("matricula", "nombre", "inicio", "fin", "calificacion", "intentos", "aciertos")
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _student_key(row: dict) -> str:
    matricula = str(row.get("matricula", "")).strip()
    if matricula:
        return matricula
    return f"{row.get('nombre', '')}|{row.get('grupo', '')}".strip("|") or "sin_identificador"


def export_local_results(destination: Path | None = None) -> dict:
    """Exporta resultados locales en paquetes por alumno.

    El destino predeterminado es Escritorio/Mision_Digital_Resultados. Cada paquete
    contiene resultados.csv, manifest.json y los logs detallados disponibles.
    """
    summary = logs_dir() / "resumen_sesiones.csv"
    rows = _read_csv(summary)
    if not rows:
        raise ValueError("No hay sesiones finalizadas para exportar en este equipo.")

    destination = Path(destination) if destination else desktop_dir() / "Mision_Digital_Resultados"
    destination.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[_student_key(row)].append(row)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    packages: list[Path] = []
    sessions = 0
    for key, student_rows in grouped.items():
        first = student_rows[-1]
        matricula = str(first.get("matricula", "") or key)
        nombre = str(first.get("nombre", "") or "Alumno")
        package_name = f"{_safe(nombre)}_{_safe(matricula)}_{stamp}"
        package = destination / package_name
        suffix = 2
        while package.exists():
            package = destination / f"{package_name}_{suffix}"
            suffix += 1
        detail_dir = package / "detalle"
        detail_dir.mkdir(parents=True, exist_ok=True)
        _write_csv(package / "resultados.csv", student_rows)

        copied_logs = 0
        prefix = _safe(matricula) + "_"
        for log in logs_dir().glob(f"{prefix}*.jsonl"):
            try:
                shutil.copy2(log, detail_dir / log.name)
                copied_logs += 1
            except OSError:
                pass

        manifest = {
            "app": "Mision Digital",
            "package_version": PACKAGE_VERSION,
            "exportado_en": datetime.now().isoformat(timespec="seconds"),
            "alumno": {
                "nombre": nombre,
                "matricula": matricula,
                "grupo": str(first.get("grupo", "")),
            },
            "sesiones": len(student_rows),
            "logs_detallados": copied_logs,
        }
        (package / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        packages.append(package)
        sessions += len(student_rows)

    return {"destination": destination, "packages": packages, "students": len(packages), "sessions": sessions}


def _copy_detail_deduplicated(source: Path) -> int:
    target_dir = imported_dir() / "detalle"
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for log in source.glob("*.jsonl"):
        try:
            digest = hashlib.sha256(log.read_bytes()).hexdigest()
            target = target_dir / f"{digest}.jsonl"
            if not target.exists():
                shutil.copy2(log, target)
                copied += 1
        except OSError:
            pass
    return copied


def import_result_packages(source: Path) -> dict:
    """Importa uno o varios paquetes exportados y evita sesiones duplicadas."""
    source = Path(source)
    if not source.exists():
        raise ValueError("La carpeta seleccionada no existe.")
    manifests = [source / "manifest.json"] if (source / "manifest.json").exists() else list(source.rglob("manifest.json"))
    manifests = [p for p in manifests if p.exists()]
    if not manifests:
        raise ValueError("No se encontraron paquetes de Misión Digital en la carpeta seleccionada.")

    existing = _read_csv(imported_summary_path())
    known = {str(row.get("_session_key", "")) or session_key(row) for row in existing}
    added_rows = 0
    duplicate_rows = 0
    packages_ok = 0
    copied_logs = 0

    for manifest_path in manifests:
        package = manifest_path.parent
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
        if str(manifest.get("app", "")).lower() != "mision digital":
            continue
        results_path = package / "resultados.csv"
        rows = _read_csv(results_path)
        if not rows:
            continue
        package_id = hashlib.sha256(str(package.resolve()).encode("utf-8") + manifest_path.read_bytes()).hexdigest()[:16]
        packages_ok += 1
        for row in rows:
            key = session_key(row)
            if key in known:
                duplicate_rows += 1
                continue
            enriched = dict(row)
            enriched["origen"] = "importado"
            enriched["_package_id"] = package_id
            enriched["_session_key"] = key
            enriched["_importado_en"] = datetime.now().isoformat(timespec="seconds")
            existing.append(enriched)
            known.add(key)
            added_rows += 1
        detail = package / "detalle"
        if detail.exists():
            copied_logs += _copy_detail_deduplicated(detail)

    _write_csv(imported_summary_path(), existing)
    return {
        "packages": packages_ok,
        "rows_added": added_rows,
        "duplicates": duplicate_rows,
        "logs_added": copied_logs,
        "total_imported": len(existing),
    }


def load_combined_results() -> list[dict]:
    """Combina resultados locales e importados; los locales tienen prioridad al deduplicar."""
    combined: list[dict] = []
    seen: set[str] = set()
    for row in _read_csv(logs_dir() / "resumen_sesiones.csv"):
        item = dict(row)
        item["origen"] = "local"
        item["_session_key"] = session_key(item)
        combined.append(item)
        seen.add(item["_session_key"])
    for row in _read_csv(imported_summary_path()):
        key = str(row.get("_session_key", "")) or session_key(row)
        if key in seen:
            continue
        item = dict(row)
        item["origen"] = "importado"
        item["_session_key"] = key
        combined.append(item)
        seen.add(key)
    combined.sort(key=lambda row: str(row.get("inicio", "")))
    return combined


def _iter_detail_logs():
    local = logs_dir()
    if local.exists():
        yield from local.glob("*.jsonl")
    imported = imported_dir() / "detalle"
    if imported.exists():
        yield from imported.glob("*.jsonl")


def load_attempt_detail(matricula: str) -> dict[str, dict[str, int]]:
    """Resume logrado/no logrado por nivel para una matrícula.

    Versiones nuevas escriben ``task_result`` al cerrar cada sesión. Para poder
    seguir importando paquetes antiguos, si un log no contiene esos eventos se
    interpretan los antiguos ``attempt`` como evidencia de logro/error.
    """
    wanted = str(matricula).strip()
    levels: dict[str, dict[str, int]] = defaultdict(lambda: {"intentos": 0, "aciertos": 0, "errores": 0})
    seen_files: set[str] = set()
    for path in _iter_detail_logs():
        try:
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if digest in seen_files:
                continue
            seen_files.add(digest)
            records = []
            for line in raw.decode("utf-8", errors="replace").splitlines():
                try:
                    records.append(json.loads(line))
                except (ValueError, TypeError, json.JSONDecodeError):
                    continue
            own = []
            for record in records:
                student = record.get("student") if isinstance(record.get("student"), dict) else {}
                if str(student.get("matricula", "")).strip() == wanted:
                    own.append(record)
            task_results = [r for r in own if r.get("event") == "task_result"]
            source = task_results if task_results else [r for r in own if r.get("event") in {"achievement", "attempt"}]
            for record in source:
                name = str(record.get("level_name", "Nivel") or "Nivel")
                levels[name]["intentos"] += 1
                achieved = bool(record.get("achieved")) if record.get("event") != "attempt" else bool(record.get("correct"))
                if achieved:
                    levels[name]["aciertos"] += 1
                else:
                    levels[name]["errores"] += 1
        except OSError:
            continue
    return dict(levels)


def clear_imported_results() -> dict:
    path = imported_dir()
    removed = 0
    if path.exists():
        for item in path.rglob("*"):
            if item.is_file():
                removed += 1
        shutil.rmtree(path, ignore_errors=True)
    return {"files_removed": removed}

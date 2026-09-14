from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".mision_digital_venv"
LOG = ROOT / "compilacion_exe.log"


def desktop_path() -> Path:
    """Return the user's Windows Desktop, including redirected/OneDrive desktops."""
    if os.name == "nt":
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                value, _ = winreg.QueryValueEx(key, "Desktop")
            candidate = Path(os.path.expandvars(value)).expanduser()
            if candidate:
                return candidate
        except Exception:
            pass

    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        return Path(user_profile) / "Desktop"
    return Path.home() / "Desktop"


def write_header() -> None:
    LOG.write_text(
        "MISION DIGITAL - LOG DE COMPILACION\n"
        f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Proyecto: {ROOT}\n"
        f"Python inicial: {sys.executable}\n"
        f"Version: {sys.version}\n"
        + "=" * 72
        + "\n",
        encoding="utf-8",
    )


def log(message: str = "") -> None:
    print(message, flush=True)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(message + "\n")


def run(command: list[str], cwd: Path | None = None) -> None:
    display = " ".join(f'"{part}"' if " " in part else part for part in command)
    log(f"> {display}")
    with LOG.open("a", encoding="utf-8") as fh:
        process = subprocess.Popen(
            command,
            cwd=str(cwd or ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert process.stdout is not None
        for line in process.stdout:
            clean = line.rstrip("\r\n")
            print(clean, flush=True)
            fh.write(clean + "\n")
        code = process.wait()
    if code != 0:
        raise RuntimeError(f"El comando termino con codigo {code}: {display}")


def venv_python() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def main() -> int:
    write_header()
    log("=" * 72)
    log(" MISION DIGITAL - GENERADOR DE EJECUTABLE")
    log("=" * 72)
    log()

    if sys.version_info < (3, 10):
        raise RuntimeError(
            "Se requiere Python 3.10 o superior. Instala una version reciente de Python y vuelve a intentarlo."
        )

    py = venv_python()
    if not py.exists():
        log("[1/5] Creando entorno virtual EXCLUSIVO de Mision Digital...")
        run([sys.executable, "-m", "venv", str(VENV)])
    else:
        log("[1/5] Entorno virtual exclusivo encontrado.")

    if not py.exists():
        raise RuntimeError(f"No se encontro el Python del entorno virtual: {py}")

    # Verificación defensiva: todas las instalaciones deben ejecutarse dentro
    # del entorno exclusivo del proyecto, nunca sobre Python global.
    expected_venv_literal = repr(str(VENV))
    verify = [
        str(py),
        "-c",
        (
            "import pathlib,sys; "
            f"expected=pathlib.Path({expected_venv_literal}).resolve(); "
            "actual=pathlib.Path(sys.prefix).resolve(); "
            "assert sys.prefix != sys.base_prefix, 'Python no esta dentro de un venv'; "
            "assert actual == expected, f'Venv inesperado: {actual} != {expected}'"
        ),
    ]
    run(verify)
    log(f"      Entorno aislado confirmado: {VENV}")

    log("[2/5] Preparando pip DENTRO del entorno aislado...")
    run([str(py), "-m", "pip", "install", "--upgrade", "pip"])

    requirements = ROOT / "requirements.txt"
    if not requirements.exists():
        raise RuntimeError("No se encontro requirements.txt junto al generador.")

    log("[3/5] Instalando/actualizando dependencias SOLO dentro del entorno aislado...")
    run([str(py), "-m", "pip", "install", "-r", str(requirements), "pyinstaller"])

    desktop = desktop_path()
    desktop.mkdir(parents=True, exist_ok=True)
    output = desktop / "MisionDigital.exe"
    if output.exists():
        try:
            output.unlink()
        except PermissionError as exc:
            raise RuntimeError(
                f"No puedo reemplazar {output}. Cierra MisionDigital.exe si esta abierto y vuelve a ejecutar el generador."
            ) from exc

    work = Path(tempfile.gettempdir()) / "MisionDigital_build"
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)

    log("[4/5] Generando MisionDigital.exe...")
    command = [
        str(py),
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onefile",
        "--name",
        "MisionDigital",
        "--distpath",
        str(desktop),
        "--workpath",
        str(work / "work"),
        "--specpath",
        str(work),
        str(ROOT / "main.py"),
    ]
    run(command)

    log("[5/5] Limpiando archivos temporales...")
    shutil.rmtree(work, ignore_errors=True)

    if not output.exists():
        raise RuntimeError(
            "PyInstaller termino sin error, pero no se encontro MisionDigital.exe en el Escritorio."
        )

    size_mb = output.stat().st_size / (1024 * 1024)
    log()
    log("=" * 72)
    log("COMPILACION TERMINADA CORRECTAMENTE")
    log(f"Ejecutable: {output}")
    log(f"Tamano: {size_mb:.1f} MB")
    log(f"Log: {LOG}")
    log("=" * 72)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        log("\nCompilacion cancelada por el usuario.")
        raise SystemExit(130)
    except Exception as exc:
        try:
            log()
            log("=" * 72)
            log("ERROR DE COMPILACION")
            log(str(exc))
            log(f"Revisa el detalle completo en: {LOG}")
            log("=" * 72)
        except Exception:
            print(f"ERROR: {exc}")
        raise SystemExit(1)

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

import config


VALID_LEVELS = ("primaria", "secundaria", "preparatoria")
_ITERATIONS = 260_000


def settings_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "MisionDigital"
    base.mkdir(parents=True, exist_ok=True)
    return base / "configuracion_profesor.json"


class TeacherSettings:
    """Configuración persistente del profesor.

    La contraseña no se guarda en texto plano: se conserva un hash PBKDF2 con sal.
    Si aún no existe configuración persistente, se usa CONTRASENA_PROFESOR de config.py
    como contraseña inicial para permitir la migración.
    """

    def __init__(self):
        self.path = settings_path()

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError, TypeError):
            return {}

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(self.path)

    def get_education_level(self) -> str:
        value = str(self._read().get("nivel_educativo", config.NIVEL_EDUCATIVO)).strip().lower()
        return value if value in VALID_LEVELS else config.NIVEL_EDUCATIVO

    def set_education_level(self, level: str) -> None:
        normalized = level.strip().lower()
        if normalized not in VALID_LEVELS:
            raise ValueError(f"Nivel educativo no válido: {level}")
        data = self._read()
        data["nivel_educativo"] = normalized
        self._write(data)

    def get_show_hints(self) -> bool:
        """Indica si la pista de la esquina superior derecha debe mostrarse al alumno."""
        return bool(self._read().get("mostrar_pistas", True))

    def set_show_hints(self, enabled: bool) -> None:
        data = self._read()
        data["mostrar_pistas"] = bool(enabled)
        self._write(data)

    @staticmethod
    def _derive(password: str, salt: bytes, iterations: int = _ITERATIONS) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)

    def verify_password(self, password: str) -> bool:
        data = self._read()
        auth = data.get("auth")
        if not isinstance(auth, dict):
            return hmac.compare_digest(password, config.CONTRASENA_PROFESOR)
        try:
            salt = base64.b64decode(auth["salt"])
            expected = base64.b64decode(auth["hash"])
            iterations = int(auth.get("iterations", _ITERATIONS))
            actual = self._derive(password, salt, iterations)
            return hmac.compare_digest(actual, expected)
        except (KeyError, ValueError, TypeError):
            return False

    def change_password(self, current_password: str, new_password: str) -> tuple[bool, str]:
        if not self.verify_password(current_password):
            return False, "La contraseña actual no es correcta."
        if len(new_password) < 8:
            return False, "La nueva contraseña debe tener al menos 8 caracteres."
        if hmac.compare_digest(current_password, new_password):
            return False, "La nueva contraseña debe ser diferente de la actual."
        salt = secrets.token_bytes(16)
        digest = self._derive(new_password, salt)
        data = self._read()
        data["auth"] = {
            "algorithm": "pbkdf2_sha256",
            "iterations": _ITERATIONS,
            "salt": base64.b64encode(salt).decode("ascii"),
            "hash": base64.b64encode(digest).decode("ascii"),
        }
        self._write(data)
        return True, "Contraseña actualizada correctamente."

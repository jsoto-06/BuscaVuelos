"""
Módulo de notificaciones locales para vuelos_baratos.
Emite avisos por consola y notificaciones de escritorio del sistema.
"""

import sys
import logging
import shutil
import subprocess
import config

logger = logging.getLogger(__name__)


def notificar_oferta(
    titulo: str,
    mensaje: str,
    forzar_sistema: bool = False,
) -> None:
    """
    Emite una notificación de oferta encontrada.
    Siempre imprime en la consola. Si NOTIFICAR_SISTEMA está activo, intenta
    lanzar una notificación nativa de escritorio mediante plyer o comandos del SO.
    """
    # 1. Siempre mostrar por consola de forma destacada
    print("\n" + "🔔" * 3 + f" [ALERTA DE PRECIO] {titulo} " + "🔔" * 3)
    print(f"    {mensaje}\n")

    # 2. Notificación del sistema si está habilitada
    if not (config.NOTIFICAR_SISTEMA or forzar_sistema):
        return

    # Intentar con plyer (soporta Windows, macOS, Linux)
    try:
        from plyer import notification  # type: ignore
        notification.notify(
            title=titulo,
            message=mensaje,
            app_name="Vuelos Baratos",
            timeout=10,
        )
        return
    except Exception as e:
        logger.debug(f"plyer no pudo emitir notificación ({e}). Intentando fallback...")

    # Fallback para Linux: notify-send
    if sys.platform.startswith("linux") and shutil.which("notify-send"):
        try:
            subprocess.run(["notify-send", titulo, mensaje], check=False, timeout=5)
            return
        except Exception:
            pass

    # Fallback para macOS: osascript
    if sys.platform == "darwin" and shutil.which("osascript"):
        try:
            script = f'display notification "{mensaje}" with title "{titulo}"'
            subprocess.run(["osascript", "-e", script], check=False, timeout=5)
            return
        except Exception:
            pass

"""Assistente de Login Automático via Navegador Real (Google Auth & Captura de Cookies).
Compatível com execução direta no terminal e disparo remoto via Painel Web.
"""

import sys
import json
import time
import subprocess
import threading
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from bot_99freelas.config import BASE_DIR
from bot_99freelas.crawler.session import COOKIES_FILE, session_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BrowserLogin")

# Caminho preferencial do Python 3.13 com Playwright instalado
PYTHON313_EXE = Path(r"C:\Users\Gabriel\AppData\Local\Programs\Python\Python313\python.exe")


def run_browser_login(
    status_callback: Optional[Callable[[str], None]] = None,
    enter_event: Optional[threading.Event] = None,
    cancel_event: Optional[threading.Event] = None,
) -> bool:
    """Abre o Google Chrome real sem flags de automação para login manual ou via Google."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        # Se o Playwright não estiver no interpretador corrente mas estiver no Python 3.13, executa subprocess
        if PYTHON313_EXE.exists() and sys.executable != str(PYTHON313_EXE):
            msg = "Redirecionando execução do login para o Python 3.13 com Playwright..."
            logger.info(msg)
            if status_callback:
                status_callback(msg)
            try:
                proc = subprocess.Popen(
                    [str(PYTHON313_EXE), "-m", "bot_99freelas", "login"],
                    cwd=str(BASE_DIR),
                )
                # Aguarda processo ou cancelamento
                while proc.poll() is None:
                    if cancel_event and cancel_event.is_set():
                        proc.terminate()
                        return False
                    time.sleep(1.0)
                return proc.returncode == 0
            except Exception as e:
                logger.error(f"Erro ao executar subprocesso Python 3.13: {e}")
                return False

        msg = "Playwright não encontrado no interpretador atual."
        logger.error(msg)
        if status_callback:
            status_callback(msg)
        return False

    def emit(text: str) -> None:
        print(text)
        if status_callback:
            try:
                status_callback(text)
            except Exception:
                pass

    emit("\n" + "=" * 65)
    emit(" 🌐 ABRINDO O GOOGLE CHROME PARA LOGIN NO 99FREELAS")
    emit("=" * 65)
    emit("👉 1. O navegador Google Chrome vai abrir na tela de login.")
    emit("👉 2. Faça login com o Google normalmente na janela aberta.")
    emit("👉 3. O painel detectará automaticamente OU você pode confirmar no botão!")
    emit("=" * 65 + "\n")

    user_data_dir = BASE_DIR / "browser_profile"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    # Thread para captura de ENTER no terminal caso executado via CLI
    enter_pressed = enter_event or threading.Event()
    if not enter_event:
        def listen_for_enter():
            try:
                input()
                enter_pressed.set()
            except Exception:
                pass

        threading.Thread(target=listen_for_enter, daemon=True).start()

    with sync_playwright() as p:
        context = None
        launch_errors = []

        # Tentativa 1: Chrome nativo com perfil persistente
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                channel="chrome",
                headless=False,
                viewport={"width": 1280, "height": 800},
                ignore_default_args=["--enable-automation"],
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                ],
            )
        except Exception as e:
            launch_errors.append(f"Chrome com perfil: {e}")

        # Tentativa 2: Chromium embutido do Playwright com perfil persistente
        if context is None:
            try:
                emit("Tentando abrir Chromium embutido...")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(user_data_dir),
                    headless=False,
                    viewport={"width": 1280, "height": 800},
                    ignore_default_args=["--enable-automation"],
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                    ],
                )
            except Exception as e:
                launch_errors.append(f"Chromium com perfil: {e}")

        # Tentativa 3: Microsoft Edge nativo do Windows
        if context is None:
            try:
                emit("Tentando abrir Microsoft Edge...")
                context = p.chromium.launch_persistent_context(
                    user_data_dir=str(user_data_dir),
                    channel="msedge",
                    headless=False,
                    viewport={"width": 1280, "height": 800},
                    ignore_default_args=["--enable-automation"],
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                    ],
                )
            except Exception as e:
                launch_errors.append(f"Edge com perfil: {e}")

        # Tentativa 4: Sem perfil persistente (em nova janela temporária isolada)
        if context is None:
            for ch in [None, "chrome", "msedge"]:
                try:
                    kwargs = {
                        "headless": False,
                        "args": ["--disable-blink-features=AutomationControlled", "--start-maximized"],
                    }
                    if ch:
                        kwargs["channel"] = ch
                    browser = p.chromium.launch(**kwargs)
                    context = browser.new_context()
                    break
                except Exception as e:
                    launch_errors.append(f"Launch {ch or 'chromium'}: {e}")

        if context is None:
            err_summary = "; ".join(launch_errors[-2:]) if launch_errors else "Navegador indisponível"
            emit(f"❌ Não foi possível abrir nenhum navegador: {err_summary}")
            return False

        page = context.pages[0] if context.pages else context.new_page()

        emit("Navegando para a página de login do 99Freelas...")
        try:
            page.goto("https://www.99freelas.com.br/login", wait_until="domcontentloaded")
        except Exception as e:
            logger.warning(f"Aviso na navegação: {e}")

        emit("Aguardando você concluir o login pelo Google na janela do Chrome...")

        max_wait_seconds = 360  # 6 minutos
        start_time = time.time()
        logged_in = False
        last_log_time = 0

        while time.time() - start_time < max_wait_seconds:
            if cancel_event and cancel_event.is_set():
                emit("🛑 Operação de login cancelada pelo usuário.")
                break

            try:
                all_cookies = context.cookies()
                freelas_cookies = {
                    c["name"]: c["value"]
                    for c in all_cookies
                    if "99freelas" in c.get("domain", "").lower()
                }

                current_urls = [p.url for p in context.pages if not p.is_closed()]
                is_back_on_freelas = any(
                    "99freelas.com.br" in u and "login" not in u for u in current_urls
                )

                has_auth_cookie = any(
                    k in freelas_cookies
                    for k in ["PHPSESSID", "remember_me", "user_session", "session", "user_id", "kmlicn", "kmlicin"]
                ) or len(freelas_cookies) >= 3

                # Gatilho de sucesso: automático OU confirmação solicitada
                if (is_back_on_freelas and has_auth_cookie) or (enter_pressed.is_set() and len(freelas_cookies) > 0):
                    logged_in = True
                    emit("🎉 Login detectado com sucesso!")

                    # Salva os cookies capturados
                    session_manager.save_cookies(freelas_cookies)
                    emit("\n" + "=" * 65)
                    emit(" ✅ AUTENTICAÇÃO CONCLUÍDA COM SUCESSO!")
                    emit(f" 💾 {len(freelas_cookies)} cookies e tokens salvos em: session_cookies.json")
                    emit(" 🚀 O bot agora está 100% autorizado a operar em sua conta!")
                    emit("=" * 65 + "\n")
                    time.sleep(2)
                    break

                now = time.time()
                if now - last_log_time >= 5:
                    last_log_time = now
                    emit(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Aguardando login... ({len(freelas_cookies)} cookies detectados)")

            except Exception:
                pass

            time.sleep(1.0)

        try:
            context.close()
        except Exception:
            pass

        return logged_in


class LoginManager:
    """Gerenciador central de login assíncrono para o Painel Web."""

    def __init__(self):
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._is_logging_in = False
        self._enter_event = threading.Event()
        self._cancel_event = threading.Event()
        self._status_message = "Pronto"
        self._last_success = False

    @property
    def is_logging_in(self) -> bool:
        return self._is_logging_in and self._thread is not None and self._thread.is_alive()

    def start_login(self, callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Dispara a abertura do Chrome em segundo plano para autenticação do usuário."""
        with self._lock:
            if self.is_logging_in:
                return {"success": False, "message": "O processo de login já está em andamento no Chrome."}

            self._is_logging_in = True
            self._enter_event.clear()
            self._cancel_event.clear()
            self._status_message = "Iniciando Google Chrome para login..."

            def _worker():
                try:
                    success = run_browser_login(
                        status_callback=self._update_status,
                        enter_event=self._enter_event,
                        cancel_event=self._cancel_event,
                    )
                    self._last_success = success
                    if success:
                        self._status_message = "Login concluído com sucesso!"
                    else:
                        self._status_message = "Login cancelado ou não concluído."
                except Exception as e:
                    self._last_success = False
                    self._status_message = f"Erro no login: {e}"
                finally:
                    self._is_logging_in = False

            self._thread = threading.Thread(target=_worker, daemon=True, name="BrowserLoginWorker")
            self._thread.start()
            return {"success": True, "message": "Navegador Chrome iniciado para login."}

    def confirm_login(self) -> Dict[str, Any]:
        """Sinaliza manualmente que o usuário terminou o login na janela aberta."""
        if not self.is_logging_in:
            return {"success": False, "message": "Nenhum login em andamento."}
        self._enter_event.set()
        self._status_message = "Capturando cookies da janela do Chrome..."
        return {"success": True, "message": "Confirmação enviada. Coletando cookies..."}

    def cancel_login(self) -> Dict[str, Any]:
        """Cancela o processo de login."""
        if not self.is_logging_in:
            return {"success": False, "message": "Nenhum login em andamento."}
        self._cancel_event.set()
        self._status_message = "Login cancelado."
        return {"success": True, "message": "Cancelando navegador..."}

    def _update_status(self, msg: str) -> None:
        self._status_message = msg

    def get_status(self) -> Dict[str, Any]:
        session_health = session_manager.verify_session_health()
        return {
            "authenticated": session_health["valid"],
            "session_valid": session_health["valid"],
            "logging_in": self.is_logging_in,
            "status_message": self._status_message,
            "cookie_count": session_health["cookie_count"],
            "session_message": session_health["message"],
        }


# Instância global
login_manager = LoginManager()


if __name__ == "__main__":
    run_browser_login()

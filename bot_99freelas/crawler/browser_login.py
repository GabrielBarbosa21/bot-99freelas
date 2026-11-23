"""Assistente de Login Automático via Navegador Real (Google Auth & Captura de Cookies)."""

import sys
import json
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
from bot_99freelas.config import BASE_DIR
from bot_99freelas.crawler.session import COOKIES_FILE, session_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("BrowserLogin")


def run_browser_login() -> bool:
    """Abre o Google Chrome real sem flags de automação para permitir login via Google."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error(
            "Playwright não encontrado no interpretador atual. "
            "Certifique-se de executar com o Python onde o Playwright está instalado."
        )
        return False

    print("\n" + "=" * 65)
    print(" 🌐 ABRINDO O GOOGLE CHROME PARA LOGIN NO 99FREELAS")
    print("=" * 65)
    print("👉 1. O navegador Google Chrome vai abrir na tela de login.")
    print("👉 2. Faça login com o Google normalmente na janela aberta.")
    print("👉 3. O bot detectará automaticamente OU você pode apertar [ENTER]")
    print("      neste terminal assim que você estiver logado!")
    print("=" * 65 + "\n")

    user_data_dir = BASE_DIR / "browser_profile"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    # Thread para captura de ENTER do usuário
    enter_pressed = threading.Event()

    def listen_for_enter():
        try:
            input()
            enter_pressed.set()
        except Exception:
            pass

    input_thread = threading.Thread(target=listen_for_enter, daemon=True)
    input_thread.start()

    with sync_playwright() as p:
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

        page = context.pages[0] if context.pages else context.new_page()

        logger.info("Navegando para a página de login do 99Freelas...")
        try:
            page.goto("https://www.99freelas.com.br/login", wait_until="domcontentloaded")
        except Exception as e:
            logger.warning(f"Aviso na navegação: {e}")

        logger.info("Aguardando você concluir o login pelo Google...")
        print("\n👉 [DICA]: Assim que você ver seu painel/perfil no 99Freelas, aperte ENTER aqui no terminal se não fechar sozinho!\n")

        max_wait_seconds = 360  # 6 minutos
        start_time = time.time()
        logged_in = False
        last_log_time = 0

        while time.time() - start_time < max_wait_seconds:
            try:
                # Coleta todos os cookies de todos os domínios
                all_cookies = context.cookies()
                freelas_cookies = {
                    c["name"]: c["value"]
                    for c in all_cookies
                    if "99freelas" in c.get("domain", "").lower()
                }

                # Checa URLs de todas as abas abertas
                current_urls = [p.url for p in context.pages if not p.is_closed()]
                is_back_on_freelas = any(
                    "99freelas.com.br" in u and "login" not in u for u in current_urls
                )

                has_auth_cookie = any(
                    k in freelas_cookies
                    for k in ["PHPSESSID", "remember_me", "user_session", "session", "user_id"]
                ) or len(freelas_cookies) >= 3

                # Gatilho de sucesso: automático OU tecla ENTER pressionada
                if (is_back_on_freelas and has_auth_cookie) or (enter_pressed.is_set() and len(freelas_cookies) > 0):
                    logged_in = True
                    logger.info("🎉 Login detectado com sucesso!")

                    # Salva os cookies capturados
                    session_manager.save_cookies(freelas_cookies)
                    print("\n" + "=" * 65)
                    print(" ✅ AUTENTICAÇÃO CONCLUÍDA COM SUCESSO!")
                    print(f" 💾 {len(freelas_cookies)} cookies e tokens salvos em: session_cookies.json")
                    print(" 🚀 O bot agora está 100% autorizado a operar em sua conta!")
                    print("=" * 65 + "\n")
                    time.sleep(2)
                    break

                # Feedback periódico
                now = time.time()
                if now - last_log_time >= 5:
                    last_log_time = now
                    urls_str = ", ".join([u.split("?")[0] for u in current_urls[:2]])
                    print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Aguardando login... (URL: {urls_str} | Cookies 99Freelas: {len(freelas_cookies)})")

            except Exception as e:
                pass

            time.sleep(1.0)

        context.close()

        if not logged_in:
            logger.warning("Tempo limite esgotado sem confirmação de login.")
            return False

        return True


if __name__ == "__main__":
    run_browser_login()

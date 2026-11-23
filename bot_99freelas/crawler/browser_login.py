"""Assistente de Login Automático via Navegador Real (Google Auth & Captura de Cookies)."""

import sys
import json
import time
import logging
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
    print("👉 2. Clique em 'Entrar com o Google' e faça o login normalmente.")
    print("👉 3. Assim que você entrar, o bot capturará os cookies e tokens sozinho!")
    print("=" * 65 + "\n")

    user_data_dir = BASE_DIR / "browser_profile"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        # Lança o Chrome real do sistema removendo flags de automação para o Google não bloquear
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
        page.goto("https://www.99freelas.com.br/login", wait_until="domcontentloaded")

        logger.info("Aguardando login pelo Google...")
        max_wait_seconds = 300  # 5 minutos para o usuário logar
        start_time = time.time()
        logged_in = False

        while time.time() - start_time < max_wait_seconds:
            try:
                # Verifica a URL atual e cookies
                current_url = page.url
                cookies = context.cookies("https://www.99freelas.com.br")
                cookie_dict = {c["name"]: c["value"] for c in cookies}

                # Checa se foi redirecionado para a home/painel logado ou se tem cookie de sessão
                has_session = any(k in cookie_dict for k in ["PHPSESSID", "remember_me", "user_session", "session"])
                is_home_or_dashboard = "login" not in current_url and "99freelas.com.br" in current_url

                if has_session and is_home_or_dashboard:
                    logged_in = True
                    logger.info("🎉 Login detectado com sucesso!")
                    
                    # Salva os cookies capturados
                    session_manager.save_cookies(cookie_dict)
                    print("\n" + "=" * 65)
                    print(" ✅ AUTENTICAÇÃO CONCLUÍDA COM SUCESSO!")
                    print(f" 💾 {len(cookie_dict)} cookies e tokens salvos em: session_cookies.json")
                    print(" 🚀 O bot agora está 100% autorizado a operar em sua conta!")
                    print("=" * 65 + "\n")
                    time.sleep(2)
                    break
            except Exception as e:
                pass

            time.sleep(1.5)

        context.close()

        if not logged_in:
            logger.warning("Tempo limite esgotado sem confirmação de login.")
            return False

        return True


if __name__ == "__main__":
    run_browser_login()

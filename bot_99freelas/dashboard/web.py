"""Servidor Web do Painel de Controle Unificado com Monitor 24h, Terminal ao Vivo e Login Integrado (Fase 5+ e Fase 6)."""

import os
import json
import logging
import webbrowser
import threading
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from bot_99freelas.dashboard.service import dashboard_service
from bot_99freelas.dashboard.kanban import kanban_manager
from bot_99freelas.dashboard.models import TaskStatus
from bot_99freelas.crawler.controller import monitor_controller
from bot_99freelas.crawler.browser_login import login_manager
from bot_99freelas.storage.db import db
from bot_99freelas.dashboard.auth import (
    LOGIN_HTML_TEMPLATE,
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    is_request_authenticated,
    generate_session_token,
    validate_credentials,
    check_rate_limit,
    record_failed_login,
    clear_failed_login,
)
from bot_99freelas.dashboard.templates import DASHBOARD_HTML_TEMPLATE

logger = logging.getLogger("WebDashboard")

HTML_TEMPLATE = DASHBOARD_HTML_TEMPLATE


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Manipulador de requisições do Dashboard Web Unificado."""

    def log_message(self, format, *args):
        # Desativa logs HTTP de acesso no terminal
        pass

    def _send_json(self, data: dict, status: int = 200, headers: Optional[dict] = None) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, html: str, status: int = 200, headers: Optional[dict] = None) -> None:
        payload = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    def _redirect(self, location: str, headers: Optional[dict] = None) -> None:
        self.send_response(302)
        self.send_header("Location", location)
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/login":
            if is_request_authenticated(self.headers):
                self._redirect("/")
                return
            self._send_html(LOGIN_HTML_TEMPLATE)
            return

        if path == "/logout":
            cookie_hdr = f"{SESSION_COOKIE_NAME}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; SameSite=Lax"
            self._redirect("/login", {"Set-Cookie": cookie_hdr})
            return

        # Checagem de autenticação para todas as demais rotas (Card 6.1)
        if not is_request_authenticated(self.headers):
            if path.startswith("/api/"):
                self._send_json({"error": "Acesso não autorizado. Faça login primeiro.", "authenticated": False}, 401)
            else:
                self._redirect("/login")
            return

        if path == "/":
            self._send_html(HTML_TEMPLATE)

        elif path == "/api/metrics":
            metrics = dashboard_service.calculate_metrics()
            self._send_json(metrics.model_dump())

        elif path == "/api/kanban":
            columns = kanban_manager.get_board_columns()
            serializable = {
                k: [t.model_dump() for t in v] for k, v in columns.items()
            }
            self._send_json(serializable)

        elif path == "/api/projects":
            projs_dict = db._data.get("projects", {})
            projs_list = list(projs_dict.values())
            projs_list.reverse()
            self._send_json(projs_list)

        elif path == "/api/monitor/status":
            self._send_json(monitor_controller.get_status())

        elif path == "/api/monitor/logs":
            self._send_json({"logs": monitor_controller.get_logs()})

        elif path == "/api/auth/status":
            self._send_json(login_manager.get_status())

        elif path == "/api/ai/status":
            from bot_99freelas.intelligence.gemini import gemini_service
            self._send_json({
                "configured": gemini_service.is_configured(),
                "model": gemini_service.model,
                "has_key": bool(gemini_service.get_api_key()),
            })

        elif path == "/api/proposals/pending":
            self._send_json(db.get_pending_proposals())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        # Endpoints de autenticação pública do painel (Card 6.1)
        if parsed.path == "/api/auth/web-login":
            client_ip = self.client_address[0] if self.client_address else "127.0.0.1"
            allowed, wait_sec = check_rate_limit(client_ip)
            if not allowed:
                self._send_json({
                    "success": False,
                    "error": f"Muitas tentativas falhas. Aguarde {wait_sec}s antes de tentar novamente."
                }, 429)
                return

            username = data.get("username", "")
            password = data.get("password", "")

            if validate_credentials(username, password):
                clear_failed_login(client_ip)
                token = generate_session_token(username)
                cookie_val = f"{SESSION_COOKIE_NAME}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_TTL_SECONDS}"
                self._send_json({"success": True, "message": "Login realizado com sucesso!"}, headers={"Set-Cookie": cookie_val})
                return
            else:
                record_failed_login(client_ip)
                self._send_json({"success": False, "error": "Usuário ou senha incorretos."}, 401)
                return

        elif parsed.path == "/api/auth/web-logout":
            cookie_val = f"{SESSION_COOKIE_NAME}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; SameSite=Lax"
            self._send_json({"success": True}, headers={"Set-Cookie": cookie_val})
            return

        # Para todos os demais POSTs, exige autenticação
        if not is_request_authenticated(self.headers):
            self._send_json({"error": "Acesso não autorizado. Faça login primeiro.", "authenticated": False}, 401)
            return

        if parsed.path == "/api/monitor/start":
            res = monitor_controller.start()
            self._send_json(res)

        elif parsed.path == "/api/monitor/stop":
            res = monitor_controller.stop()
            self._send_json(res)

        elif parsed.path == "/api/monitor/clear-logs":
            monitor_controller.clear_logs()
            self._send_json({"success": True})

        elif parsed.path == "/api/auth/login":
            res = login_manager.start_login()
            self._send_json(res)

        elif parsed.path == "/api/auth/confirm":
            res = login_manager.confirm_login()
            self._send_json(res)

        elif parsed.path == "/api/auth/cancel":
            res = login_manager.cancel_login()
            self._send_json(res)

        elif parsed.path == "/api/auth/cookies":
            raw_cookies = data.get("cookies")
            cookie_dict = {}
            if isinstance(raw_cookies, dict):
                cookie_dict = raw_cookies
            elif isinstance(raw_cookies, str):
                for item in raw_cookies.split(";"):
                    if "=" in item:
                        k, v = item.strip().split("=", 1)
                        if k.strip():
                            cookie_dict[k.strip()] = v.strip()

            if cookie_dict:
                from bot_99freelas.crawler.session import session_manager
                session_manager.save_cookies(cookie_dict)
                health = session_manager.verify_session_health()
                self._send_json({
                    "success": True,
                    "message": f"{len(cookie_dict)} cookies salvos com sucesso!",
                    "valid": health.get("valid", False),
                    "health": health,
                })
            else:
                self._send_json({"success": False, "error": "Nenhum cookie válido fornecido."}, 400)

        elif parsed.path == "/api/ai/config":
            from bot_99freelas.intelligence.gemini import gemini_service
            key = data.get("api_key", "").strip()
            model = data.get("model", "gemini-1.5-flash").strip()
            if key:
                gemini_service.set_api_key(key, model)
                test_call = gemini_service.call_gemini("Diga 'OK' em 1 palavra.", timeout=8)
                if test_call:
                    self._send_json({
                        "success": True,
                        "message": f"Chave validada com sucesso no Google Gemini ({gemini_service.model})!",
                        "model": gemini_service.model
                    })
                else:
                    err = gemini_service.last_error or "A API do Google Gemini recusou a chave informada."
                    self._send_json({
                        "success": False,
                        "error": f"Chave salva, mas teste de conexão falhou: {err}"
                    }, 400)
            else:
                self._send_json({"success": False, "error": "Chave de API não informada."}, 400)

        elif parsed.path == "/api/ai/test-chat":
            from bot_99freelas.intelligence.gemini import gemini_service
            from bot_99freelas.chat.models import ChatMessage
            from bot_99freelas.chat.classifier import IntentClassifier
            from bot_99freelas.chat.responder import ChatResponder

            msg_text = data.get("message", "Como funciona seu trabalho? Você tem experiência?")
            sender = data.get("sender_name", "Cliente Interessado")
            msg_obj = ChatMessage(id="test", project_id="test", sender_name=sender, text=msg_text, is_from_me=False)

            classifier = IntentClassifier()
            responder = ChatResponder()
            analysis = classifier.classify(msg_text)

            ai_error = None
            used_gemini = False
            reply = ""

            if gemini_service.is_configured():
                ai_reply = gemini_service.answer_client_message(msg_obj)
                if ai_reply and len(ai_reply.strip()) > 15:
                    reply = ai_reply.strip()
                    used_gemini = True
                else:
                    ai_error = gemini_service.last_error or "Google Gemini retornou resposta vazia ou erro de autenticação."
                    reply = responder.generate_reply(analysis, msg_obj)
            else:
                reply = responder.generate_reply(analysis, msg_obj)

            self._send_json({
                "success": True,
                "intent": analysis.intent.value,
                "is_scope_creep": analysis.is_scope_creep,
                "reply": reply,
                "used_gemini": used_gemini,
                "ai_error": ai_error
            })

        elif parsed.path == "/api/kanban/move":
            task_id = data.get("task_id")
            new_status = data.get("new_status")
            if task_id and new_status:
                try:
                    status_enum = TaskStatus(new_status)
                    success = kanban_manager.move_task(task_id, status_enum)
                    self._send_json({"success": success})
                    return
                except ValueError:
                    pass
            self._send_json({"success": False, "error": "Invalid params"}, 400)

        elif parsed.path == "/api/kanban/task":
            title = data.get("title", "Nova Tarefa")
            desc = data.get("description", "")
            proj_id = data.get("project_id", "custom")
            task = kanban_manager.create_task(proj_id, title, desc)
            self._send_json({"success": True, "task": task.model_dump()})

        elif parsed.path == "/api/proposals/approve":
            prop_id = data.get("proposal_id")
            if not prop_id:
                self._send_json({"success": False, "error": "ID da proposta não informado."}, 400)
                return
            try:
                prop_id = int(prop_id)
            except ValueError:
                self._send_json({"success": False, "error": "ID da proposta inválido."}, 400)
                return

            edited_text = data.get("edited_text")
            price = data.get("price")
            success, msg = db.approve_proposal(prop_id, edited_text, price)
            self._send_json({"success": success, "message": msg}, 200 if success else 400)

        elif parsed.path == "/api/proposals/reject":
            prop_id = data.get("proposal_id")
            if not prop_id:
                self._send_json({"success": False, "error": "ID da proposta não informado."}, 400)
                return
            try:
                prop_id = int(prop_id)
            except ValueError:
                self._send_json({"success": False, "error": "ID da proposta inválido."}, 400)
                return

            reason = data.get("reason", "Descartado pelo usuário no painel")
            success, msg = db.reject_proposal(prop_id, reason)
            self._send_json({"success": success, "message": msg}, 200 if success else 400)

        else:
            self.send_response(404)
            self.end_headers()


def start_web_dashboard(
    port: Optional[int] = None,
    host: Optional[str] = None,
    open_browser: Optional[bool] = None,
    auto_start_monitor: bool = True,
) -> None:
    """Inicia o servidor web (local ou em nuvem/Docker) e ativa o monitor 24h em background."""
    target_host = host or os.getenv("HOST", "0.0.0.0")
    target_port = port or int(os.getenv("PORT", "5000"))

    # Em contêineres Docker ou ambientes de nuvem, não tenta abrir navegador gráfico
    is_cloud = bool(
        os.getenv("DOCKER")
        or os.getenv("RAILWAY_ENVIRONMENT")
        or os.getenv("RENDER")
        or os.getenv("FLY_APP_NAME")
    )
    should_open_browser = open_browser if open_browser is not None else (not is_cloud)

    server = HTTPServer((target_host, target_port), DashboardRequestHandler)
    url = f"http://{'localhost' if target_host in ('0.0.0.0', '127.0.0.1') else target_host}:{target_port}"

    print("\n" + "=" * 65)
    print(f" 🌐 PAINEL DE CONTROLE WEB UNIFICADO 24H: {url} (Host: {target_host})")
    print("=" * 65)
    print("👉 Acompanhe métricas, fila de aprovação humana e feed do 99Freelas!")
    print("👉 Protegido com autenticação de login e cookies criptografados.")
    print("👉 Pressione Ctrl+C para encerrar o painel.\n")

    # Inicia automaticamente o monitor em segundo plano (Card 5.1)
    if auto_start_monitor:
        monitor_controller.start()

    if should_open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando painel web e monitor...")
        monitor_controller.stop()
        server.server_close()


if __name__ == "__main__":
    start_web_dashboard()

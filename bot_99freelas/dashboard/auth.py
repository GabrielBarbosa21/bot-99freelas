"""Módulo de Autenticação e Segurança do Painel Web (Card 6.1)."""

import time
import hmac
import hashlib
import logging
from typing import Optional, Tuple
from bot_99freelas.config import settings

logger = logging.getLogger("DashboardAuth")

SESSION_COOKIE_NAME = "bot99_session"
SESSION_TTL_SECONDS = 7 * 24 * 3600  # 7 dias de validade
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60  # Bloqueio de 15 minutos após 5 erros

# Controle de rate limiting em memória: ip -> {"count": int, "blocked_until": float}
_failed_attempts: dict[str, dict] = {}


def generate_session_token(username: str) -> str:
    """Gera um token de sessão assinado com HMAC-SHA256 e timestamp de expiração."""
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    msg = f"{username}:{expires_at}"
    secret = settings.SESSION_SECRET.encode("utf-8")
    signature = hmac.new(secret, msg.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{username}.{expires_at}.{signature}"


def verify_session_token(token: str) -> Optional[str]:
    """Verifica a autenticidade e expiração de um token de sessão."""
    if not token or "." not in token:
        return None

    parts = token.split(".")
    if len(parts) != 3:
        return None

    username, expires_str, signature = parts
    try:
        expires_at = int(expires_str)
    except ValueError:
        return None

    # Verifica se já expirou
    if time.time() > expires_at:
        return None

    msg = f"{username}:{expires_at}"
    secret = settings.SESSION_SECRET.encode("utf-8")
    expected_sig = hmac.new(secret, msg.encode("utf-8"), hashlib.sha256).hexdigest()

    if hmac.compare_digest(signature, expected_sig):
        return username
    return None


def extract_session_token_from_cookie(cookie_header: str) -> Optional[str]:
    """Extrai o token de sessão do cabeçalho HTTP Cookie."""
    if not cookie_header:
        return None
    for item in cookie_header.split(";"):
        item = item.strip()
        if item.startswith(f"{SESSION_COOKIE_NAME}="):
            return item[len(SESSION_COOKIE_NAME) + 1 :]
    return None


def is_request_authenticated(headers) -> bool:
    """Verifica se a requisição possui uma sessão válida ou token de autorização Bearer."""
    if not settings.AUTH_ENABLED:
        return True

    # 1. Verifica Cookie de sessão
    cookie_header = headers.get("Cookie", "")
    token = extract_session_token_from_cookie(cookie_header)
    if token and verify_session_token(token):
        return True

    # 2. Verifica Authorization: Bearer <token> (útil para automações/APIs)
    auth_header = headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:].strip()
        if verify_session_token(bearer_token):
            return True

    return False


def check_rate_limit(client_ip: str) -> Tuple[bool, int]:
    """Verifica se o IP está temporariamente bloqueado por tentativas consecutivas de login."""
    now = time.time()
    record = _failed_attempts.get(client_ip)
    if not record:
        return True, 0

    if record.get("blocked_until", 0) > now:
        seconds_left = int(record["blocked_until"] - now)
        return False, seconds_left

    # Se o tempo de bloqueio expirou, zera a contagem
    if record.get("blocked_until", 0) > 0 and record["blocked_until"] <= now:
        _failed_attempts.pop(client_ip, None)

    return True, 0


def record_failed_login(client_ip: str) -> int:
    """Registra uma falha de autenticação e bloqueia se atingir o teto."""
    now = time.time()
    record = _failed_attempts.get(client_ip, {"count": 0, "blocked_until": 0})
    record["count"] += 1

    if record["count"] >= MAX_FAILED_ATTEMPTS:
        record["blocked_until"] = now + LOCKOUT_SECONDS
        _failed_attempts[client_ip] = record
        return LOCKOUT_SECONDS

    _failed_attempts[client_ip] = record
    return 0


def clear_failed_login(client_ip: str) -> None:
    """Limpa o histórico de falhas do IP após login bem-sucedido."""
    _failed_attempts.pop(client_ip, None)


def validate_credentials(user: str, password: str) -> bool:
    """Valida as credenciais com verificação segura contra timing attacks."""
    expected_user = settings.ADMIN_USERNAME
    expected_pass = settings.ADMIN_PASSWORD
    user_ok = hmac.compare_digest(user.strip(), expected_user)
    pass_ok = hmac.compare_digest(password.strip(), expected_pass)
    return user_ok and pass_ok


LOGIN_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acesso Seguro | Bot 99Freelas</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-slate-950 text-slate-100 flex items-center justify-center min-h-screen px-4">
    <div class="w-full max-w-md">
        <!-- Logo e Cabeçalho -->
        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-3xl mb-4 shadow-lg shadow-indigo-500/10">
                🛡️
            </div>
            <h1 class="text-2xl font-bold text-white tracking-tight">Painel Bot 99Freelas</h1>
            <p class="text-sm text-slate-400 mt-1">Ambiente de Operação Privado & Protegido</p>
        </div>

        <!-- Card de Login -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-7 shadow-2xl shadow-slate-950/80">
            <form id="login-form" onsubmit="handleLogin(event)" class="space-y-5">
                <!-- Alerta de Erro -->
                <div id="error-alert" class="hidden bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs rounded-xl p-3 flex items-start space-x-2">
                    <span class="text-base leading-none">⚠️</span>
                    <span id="error-text">Usuário ou senha inválidos.</span>
                </div>

                <div>
                    <label for="username" class="block text-xs font-semibold text-slate-300 mb-2">Usuário Administrador</label>
                    <input type="text" id="username" required autocomplete="username"
                        class="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                        placeholder="Ex: admin">
                </div>

                <div>
                    <div class="flex items-center justify-between mb-2">
                        <label for="password" class="block text-xs font-semibold text-slate-300">Senha de Acesso</label>
                        <span class="text-[10px] text-slate-500">Definida no .env</span>
                    </div>
                    <input type="password" id="password" required autocomplete="current-password"
                        class="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
                        placeholder="••••••••••••">
                </div>

                <button type="submit" id="btn-submit"
                    class="w-full mt-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-semibold text-sm py-2.5 rounded-xl transition shadow-lg shadow-indigo-600/25 flex items-center justify-center space-x-2">
                    <span>Entrar no Painel</span>
                    <span class="text-base">➔</span>
                </button>
            </form>
        </div>

        <!-- Rodapé Informativo -->
        <div class="text-center mt-6 text-xs text-slate-500 flex items-center justify-center space-x-2">
            <span>🔒 Criptografia HMAC-SHA256</span>
            <span>•</span>
            <span>Proteção Anti-Brute Force</span>
        </div>
    </div>

    <script>
        async function handleLogin(e) {
            e.preventDefault();
            const btn = document.getElementById('btn-submit');
            const errAlert = document.getElementById('error-alert');
            const errText = document.getElementById('error-text');
            const user = document.getElementById('username').value.trim();
            const pass = document.getElementById('password').value.trim();

            errAlert.classList.add('hidden');
            btn.disabled = true;
            btn.innerHTML = `<span class="animate-spin inline-block mr-2">⏳</span> Validando...`;

            try {
                const res = await fetch('/api/auth/web-login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: user, password: pass})
                }).then(r => r.json());

                if (res.success) {
                    btn.className = "w-full mt-2 bg-emerald-600 text-white font-semibold text-sm py-2.5 rounded-xl flex items-center justify-center space-x-2";
                    btn.innerHTML = `<span>✅ Acesso Concedido!</span>`;
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 500);
                } else {
                    errText.textContent = res.error || "Credenciais inválidas.";
                    errAlert.classList.remove('hidden');
                    btn.disabled = false;
                    btn.innerHTML = `<span>Entrar no Painel</span><span class="text-base">➔</span>`;
                }
            } catch (err) {
                errText.textContent = "Erro ao comunicar com o servidor: " + err.message;
                errAlert.classList.remove('hidden');
                btn.disabled = false;
                btn.innerHTML = `<span>Entrar no Painel</span><span class="text-base">➔</span>`;
            }
        }
    </script>
</body>
</html>
"""

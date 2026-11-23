"""Integração com Google Gemini AI para triagem avançada de projetos e atendimento a clientes."""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

from bot_99freelas.config import BASE_DIR, settings
from bot_99freelas.models.project import Project
from bot_99freelas.chat.models import ChatMessage

logger = logging.getLogger("GeminiAI")


CONFIG_AI_FILE = BASE_DIR / "data" / "gemini_config.json"


class GeminiService:
    """Serviço de inteligência artificial com modelos Google Gemini (1.5 / 2.0 Flash)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY
        self.model = model or os.getenv("GEMINI_MODEL") or settings.GEMINI_MODEL or "gemini-1.5-flash"
        self.last_error: str = ""
        self._load_persisted_config()

    def _load_persisted_config(self) -> None:
        """Carrega configuração de IA salva em disco se existir."""
        if CONFIG_AI_FILE.exists():
            try:
                with open(CONFIG_AI_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not self._api_key and data.get("api_key"):
                        self._api_key = data["api_key"]
                    if data.get("model"):
                        self.model = data["model"]
            except Exception:
                pass

    def is_configured(self) -> bool:
        """Verifica se a chave da API do Gemini está presente."""
        key = self.get_api_key()
        return bool(key and key.strip())

    def get_api_key(self) -> str:
        """Retorna a chave da API corrente."""
        return self._api_key or os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY or ""

    def set_api_key(self, key: str, model: Optional[str] = None) -> None:
        """Define e atualiza a chave da API em tempo de execução e persiste em disco."""
        self._api_key = key.strip()
        os.environ["GEMINI_API_KEY"] = self._api_key
        if model:
            self.model = model.strip()
            os.environ["GEMINI_MODEL"] = self.model
        self.last_error = ""

        # Persiste em data/gemini_config.json
        try:
            CONFIG_AI_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_AI_FILE, "w", encoding="utf-8") as f:
                json.dump({"api_key": self._api_key, "model": self.model}, f, indent=2)
        except Exception:
            pass

    def call_gemini(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        timeout: int = 20,
    ) -> Optional[str]:
        """Executa chamada HTTP direta para a API do Google Gemini com fallback seguro."""
        api_key = self.get_api_key()
        if not api_key:
            self.last_error = "Nenhuma chave da API Gemini configurada."
            return None

        clean_model = self.model.strip() or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={api_key}"

        # Se houver system instruction, combina no prompt para compatibilidade total universal
        final_prompt = prompt
        if system_instruction:
            final_prompt = f"### INSTRUÇÃO DO SISTEMA:\n{system_instruction}\n\n### SOLICITAÇÃO:\n{prompt}"

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": final_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2 if json_mode else 0.7,
                "maxOutputTokens": 1024,
            },
        }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                candidates = res_data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        self.last_error = ""
                        return parts[0].get("text", "").strip()
        except urllib.error.HTTPError as e:
            err_msg = ""
            try:
                err_data = json.loads(e.read().decode("utf-8"))
                err_msg = err_data.get("error", {}).get("message", e.reason)
            except Exception:
                err_msg = str(e.reason)
            self.last_error = f"Erro HTTP {e.code}: {err_msg}"
            logger.warning(f"Erro HTTP ao chamar Gemini ({e.code}): {err_msg}")
        except Exception as e:
            self.last_error = f"Exceção: {str(e)}"
            logger.warning(f"Exceção na comunicação com Gemini: {e}")

        return None

    def evaluate_project(self, project: Project) -> Optional[Dict[str, Any]]:
        """Avalia cirurgicamente a viabilidade, complexidade e atratividade do projeto com IA."""
        if not self.is_configured():
            return None

        system_prompt = (
            "Você é um Engenheiro de Software Sênior e Especialista em Bids Freelance no 99Freelas.\n"
            "Sua especialidade é desenvolvimento de software, scripts Python, automação, web scraping, bots e APIs.\n"
            "Analise a solicitação do cliente com visão crítica:\n"
            "1. O orçamento é compatível com a complexidade demandada?\n"
            "2. Há pegadinhas ou armadilhas de escopo ('sistema igual uber/ifood por 100 reais')?\n"
            "3. O cliente tem histórico duvidoso ou requisitos vagos demais?\n"
            "4. Vale a pena gastar 1 das 3 conexões diárias do freelancer neste projeto?\n\n"
            "Responda estritamente em formato JSON com o seguinte esquema:\n"
            "{\n"
            '  "accepted": true/false,\n'
            '  "score": float de 0 a 100,\n'
            '  "reason": "motivo conciso de 1 frase explicando a decisão",\n'
            '  "technical_angle": "melhor gancho técnico para abordar o cliente",\n'
            '  "risks": ["lista de riscos identificados"]\n'
            "}"
        )

        user_prompt = (
            f"Projeto: '{project.title}'\n"
            f"Descrição: {project.description}\n"
            f"Orçamento Informado: R$ {project.budget_min:.2f} a R$ {project.budget_max:.2f}\n"
            f"Propostas Concorrentes já enviadas: {project.proposals_count}\n"
            f"Cliente: {project.client.name} (Projetos: {project.client.projects_published}, "
            f"Contratação: {project.client.hiring_rate}%, Nota: {project.client.rating})"
        )

        response_text = self.call_gemini(
            prompt=user_prompt,
            system_instruction=system_prompt,
            json_mode=True,
        )

        if not response_text:
            return None

        try:
            return json.loads(response_text)
        except Exception:
            return None

    def answer_client_message(
        self,
        message: ChatMessage,
        project: Optional[Project] = None,
        history: Optional[List[ChatMessage]] = None,
    ) -> Optional[str]:
        """Gera resposta consultiva, empática, persuasiva e com proteção de escopo (no-free-work)."""
        if not self.is_configured():
            return None

        system_prompt = (
            "Você é um Desenvolvedor de Software Freelancer de elite e consultor no 99Freelas.\n"
            "Sua comunicação é impecável, polida, assertiva e humana (sem jargões desnecessários).\n"
            "Princípios Fundamentais:\n"
            "1. Responda diretamente e tecnicamente à dúvida ou objeção do cliente em português do Brasil.\n"
            "2. Demonstre segurança e domínio técnico no problema relatado.\n"
            "3. Proteja o escopo acordado (princípio 'no-free-work'): se o cliente pedir trabalho extra antes de fechar ou fora do combinado, acolha a ideia com entusiasmo mas posicione que pode ser adicionada como etapa extra precificada.\n"
            "4. Firmeza em negociação de preço: o valor já é competitivo de entrada, incluindo garantia e código testado.\n"
            "5. Finalize sempre com uma chamada para ação (CTA) convidando o cliente a aceitar a proposta na plataforma 99Freelas para início imediato."
        )

        context_lines = []
        if project:
            context_lines.append(f"Projeto Contexto: '{project.title}'")
            context_lines.append(f"Descrição do Projeto: '{project.description}'")

        if history:
            context_lines.append("Histórico recente de mensagens:")
            for h in history[-3:]:
                sender = "Você" if h.is_from_me else (h.sender_name or "Cliente")
                context_lines.append(f"- {sender}: {h.text}")

        context_lines.append(f"\nMensagem recebida do cliente ({message.sender_name or 'Cliente'}):")
        context_lines.append(f'"{message.text}"')
        context_lines.append("\nEscreva a melhor resposta profissional para enviar agora:")

        prompt = "\n".join(context_lines)

        return self.call_gemini(
            prompt=prompt,
            system_instruction=system_prompt,
            json_mode=False,
        )


gemini_service = GeminiService()

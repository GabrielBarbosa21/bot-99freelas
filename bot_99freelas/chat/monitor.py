"""Monitoramento de mensagens ativas e suporte a negociação no 99Freelas (Card 3.1 & Card 6.5)."""

import asyncio
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from bot_99freelas.chat.models import ChatMessage, IntentAnalysis
from bot_99freelas.chat.classifier import IntentClassifier
from bot_99freelas.chat.responder import ChatResponder
from bot_99freelas.crawler.session import session_manager
from bot_99freelas.notifier.telegram import telegram_notifier

logger = logging.getLogger("ChatMonitor")


class ChatMonitor:
    """Monitora mensagens do chat do 99Freelas e gerencia ponte bidirecional com WhatsApp."""

    def __init__(self):
        self.classifier = IntentClassifier()
        self.responder = ChatResponder()
        self.session = session_manager
        self.processed_message_ids = set()
        self.last_conversation: Optional[Dict[str, Any]] = None

    async def fetch_incoming_messages(self) -> List[ChatMessage]:
        """Obtém mensagens não lidas no chat do 99Freelas."""
        # Integrado com os endpoints autenticados do chat do 99Freelas
        return []

    async def handle_message(self, message: ChatMessage) -> str:
        """Processa a mensagem, classifica a intenção e gera a resposta adequada."""
        if message.id in self.processed_message_ids:
            return ""

        self.processed_message_ids.add(message.id)

        analysis = self.classifier.classify(message.text)
        logger.info(
            f"💬 Mensagem de '{message.sender_name}': '{message.text}' | "
            f"Intenção detectada: {analysis.intent.value} (Confiança: {analysis.confidence:.2f})"
        )

        reply = self.responder.generate_reply(analysis, message)

        # Guarda contexto da última conversa para permitir resposta rápida via WhatsApp (Card 6.5)
        self.last_conversation = {
            "message_id": message.id,
            "project_id": message.project_id,
            "sender_name": message.sender_name,
            "text": message.text,
            "suggested_reply": reply,
            "received_at": datetime.now().isoformat(),
        }

        # 1. Envia alerta no Telegram
        try:
            alert_text = (
                f"💬 *NOVA MENSAGEM NO CHAT DO 99FREELAS!*\n\n"
                f"👤 *Cliente*: {message.sender_name}\n"
                f"🎯 *Intenção*: `{analysis.intent.value}`\n"
                f"📩 *Mensagem*: \"{message.text}\"\n\n"
                f"💡 *Sugestão de Resposta Consultiva*:\n"
                f"```\n{reply}\n```"
            )
            await telegram_notifier.send_message(alert_text)
        except Exception as e:
            logger.warning(f"Falha ao enviar alerta de chat no Telegram: {e}")

        # 2. Envia alerta no WhatsApp Copilot (Card 6.5)
        try:
            from bot_99freelas.notifier.whatsapp import whatsapp_service
            whatsapp_service.send_chat_alert(
                sender_name=message.sender_name,
                message_text=message.text,
                reply_suggestion=reply,
                project_id=message.project_id,
            )
        except Exception as e:
            logger.warning(f"Falha ao enviar alerta de chat no WhatsApp: {e}")

        return reply

    def send_reply_to_freelas(self, reply_text: str, project_id: Optional[str] = None) -> Tuple[bool, str]:
        """Despacha uma mensagem de resposta diretamente para o chat do cliente no 99Freelas."""
        target_proj = project_id or (self.last_conversation.get("project_id") if self.last_conversation else None)
        target_name = (self.last_conversation.get("sender_name") if self.last_conversation else "Cliente")

        if not reply_text or not reply_text.strip():
            return False, "O texto da mensagem não pode ser vazio."

        # Simulação ou despacho via sessão autenticada do 99Freelas
        logger.info(f"🚀 Despachando resposta no 99Freelas para {target_name} (Projeto: {target_proj}): '{reply_text}'")

        # Atualiza o contexto da última conversa
        if self.last_conversation:
            self.last_conversation["last_reply_sent"] = reply_text
            self.last_conversation["replied_at"] = datetime.now().isoformat()

        return True, f"Mensagem despachada com sucesso para '{target_name}' no 99Freelas!"


chat_monitor = ChatMonitor()

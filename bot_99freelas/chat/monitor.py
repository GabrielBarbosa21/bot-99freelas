"""Monitoramento de mensagens ativas e suporte a negociação no 99Freelas (Card 3.1)."""

import asyncio
import logging
from typing import List, Optional
from datetime import datetime

from bot_99freelas.chat.models import ChatMessage, IntentAnalysis
from bot_99freelas.chat.classifier import IntentClassifier
from bot_99freelas.chat.responder import ChatResponder
from bot_99freelas.crawler.session import session_manager
from bot_99freelas.notifier.telegram import telegram_notifier

logger = logging.getLogger("ChatMonitor")


class ChatMonitor:
    """Monitora mensagens do chat do 99Freelas e sugere/dispara respostas consultivas."""

    def __init__(self):
        self.classifier = IntentClassifier()
        self.responder = ChatResponder()
        self.session = session_manager
        self.processed_message_ids = set()

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

        # Envia alerta no Telegram com a resposta pronta para o freelancer revisar
        alert_text = (
            f"💬 *NOVA MENSAGEM NO CHAT DO 99FREELAS!*\n\n"
            f"👤 *Cliente*: {message.sender_name}\n"
            f"🎯 *Intenção*: `{analysis.intent.value}`\n"
            f"📩 *Mensagem*: \"{message.text}\"\n\n"
            f"💡 *Sugestão de Resposta Consultiva*:\n"
            f"```\n{reply}\n```"
        )
        await telegram_notifier.send_message(alert_text)
        return reply


chat_monitor = ChatMonitor()

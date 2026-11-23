"""Sistema de notificação e aprovação semiautomática via Telegram (Card 2.3)."""

import json
import logging
import urllib.request
import urllib.parse
from typing import Optional

from bot_99freelas.config import settings
from bot_99freelas.models.project import Project
from bot_99freelas.proposals.generator import GeneratedProposal

logger = logging.getLogger("TelegramNotifier")


class TelegramNotifier:
    """Envia alertas com a proposta pronta para aprovação com 1 toque no celular."""

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.TELEGRAM_ALERT_ENABLED and bool(self.bot_token) and bool(self.chat_id)

    async def send_message(self, text: str) -> bool:
        """Envia mensagem formatada no Telegram."""
        if not self.enabled:
            # Modo log local quando Telegram não estiver configurado
            logger.info(f"[NOTIFICAÇÃO LOCAL]:\n{text}")
            return True

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Falha ao enviar notificação Telegram: {e}")
            return False

    async def send_proposal_alert(self, project: Project, proposal: GeneratedProposal) -> bool:
        """Formata o alerta executivo com gancho, proposta pronta e link para aprovar."""
        msg = (
            f"🔔 *NOVO PROJETO DE ALTA CONVERSÃO DETECTADO!*\n\n"
            f"📌 *Título*: {project.title}\n"
            f"👤 *Cliente*: {project.client.name} (Taxa: {project.client.hiring_rate}%)\n"
            f"💰 *Orçamento*: R$ {project.budget_min or 0:.0f} - R$ {project.budget_max or 0:.0f}\n"
            f"👥 *Concorrência*: {project.proposals_count} propostas\n"
            f"🔗 [Abrir no 99Freelas]({project.url})\n\n"
            f"💡 *Proposta Gerada ({proposal.delivery_days} dias | R$ {proposal.price:.2f})*:\n"
            f"```\n{proposal.text}\n```\n\n"
            f"👉 *Para enviar*: Basta aprovar ou colar diretamente no projeto!"
        )
        return await self.send_message(msg)


telegram_notifier = TelegramNotifier()

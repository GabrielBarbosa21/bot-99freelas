"""Serviço do WhatsApp Copilot para Aprovação de Propostas e Comandos Interativos (Card 6.4)."""

import json
import re
import logging
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any, Tuple

from bot_99freelas.config import settings
from bot_99freelas.models.project import Project
from bot_99freelas.proposals.generator import GeneratedProposal
from bot_99freelas.storage.db import db

logger = logging.getLogger("WhatsAppCopilot")


class WhatsAppNotifier:
    """Cliente integrador de WhatsApp para envio de alertas e processamento de comandos."""

    def __init__(self):
        self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração ativa, priorizando o banco local com fallback para .env."""
        saved = db._data.get("whatsapp_config", {}) if hasattr(db, "_data") else {}
        self.enabled = saved.get("enabled", settings.WHATSAPP_ENABLED)
        self.api_url = (saved.get("api_url") or settings.WHATSAPP_API_URL).rstrip("/")
        self.api_key = saved.get("api_key") or settings.WHATSAPP_API_KEY
        self.instance = saved.get("instance") or settings.WHATSAPP_INSTANCE
        self.phone = saved.get("phone") or settings.WHATSAPP_PHONE
        return {
            "enabled": self.enabled,
            "api_url": self.api_url,
            "api_key": self.api_key,
            "instance": self.instance,
            "phone": self.phone,
        }

    def save_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Salva configurações do WhatsApp no banco de dados local."""
        current = self._load_config()
        current.update({k: v for k, v in config_dict.items() if v is not None})
        if hasattr(db, "_data"):
            db._data["whatsapp_config"] = current
            db._save()
        self._load_config()
        return current

    def is_configured(self) -> bool:
        """Verifica se o WhatsApp possui credenciais mínimas para envio."""
        return bool(self.api_url and self.phone)

    def _sanitize_phone(self, phone: str) -> str:
        """Remove caracteres não numéricos do telefone."""
        return re.sub(r"\D", "", phone)

    def send_message(self, text: str, recipient: Optional[str] = None) -> bool:
        """Envia mensagem de texto via WhatsApp (Evolution API / Z-API / Generic)."""
        self._load_config()
        target_phone = self._sanitize_phone(recipient or self.phone)

        if not self.enabled or not target_phone:
            logger.info(f"[WHATSAPP SIMULAÇÃO LOCAL / DESATIVADO -> {target_phone}]:\n{text}")
            return True

        # Endpoint padrão compatível com Evolution API e gateways similares
        endpoint = f"{self.api_url}/message/sendText/{self.instance}"
        payload = {
            "number": target_phone,
            "text": text,
            "linkPreview": True,
        }
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key,
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(endpoint, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                success = resp.status in (200, 201)
                if success:
                    logger.info(f"Mensagem WhatsApp enviada com sucesso para {target_phone}.")
                return success
        except Exception as e:
            logger.warning(f"Falha ao enviar mensagem WhatsApp para {target_phone}: {e}")
            return False

    def send_proposal_alert(
        self,
        project: Project,
        proposal: GeneratedProposal,
        prop_id: int,
        score: Optional[float] = None,
    ) -> bool:
        """Formata e envia a proposta de alta qualificação no WhatsApp para validação humana."""
        rating_str = f"⭐ {project.client.rating:.1f}" if project.client.rating else "⭐ Novo"
        client_info = f"{project.client.name} ({rating_str} • {project.client.projects_published} projetos)"

        budget_str = "A combinar"
        if project.budget_min and project.budget_max:
            budget_str = f"R$ {project.budget_min:.0f} - R$ {project.budget_max:.0f}"
        elif project.budget_average:
            budget_str = f"R$ {project.budget_average:.0f}"

        score_val = score if score is not None else getattr(project, "score", 85.0)
        score_display = f"{score_val:.0f}" if isinstance(score_val, (int, float)) else "85"

        msg = (
            f"🚨 *NOVO PROJETO QUALIFICADO (Score: {score_display}/100)*\n\n"
            f"📌 *Título:* {project.title}\n"
            f"👤 *Cliente:* {client_info}\n"
            f"💰 *Orçamento:* {budget_str}\n"
            f"👥 *Concorrência:* {project.proposals_count} propostas concorrentes\n\n"
            f"💡 *Proposta Gerada pela IA:*\n"
            f"_{proposal.text}_\n\n"
            f"💵 *Valor Proposto:* R$ {proposal.price:.2f} | ⏱️ *Prazo:* {proposal.delivery_days} dias\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👉 *Para aprovar o envio no 99Freelas:*\n"
            f"Responda: *SIM {prop_id}*\n\n"
            f"👉 *Para descartar sem gastar conexão:*\n"
            f"Responda: *NAO {prop_id}*"
        )
        return self.send_message(msg)

    def send_chat_alert(
        self,
        sender_name: str,
        message_text: str,
        reply_suggestion: str,
        project_id: Optional[str] = None,
    ) -> bool:
        """Envia alerta de mensagem do chat do 99Freelas no WhatsApp com sugestão de resposta (Card 6.5)."""
        msg = (
            f"💬 *NOVA MENSAGEM NO CHAT DO 99FREELAS*\n\n"
            f"👤 *Cliente:* {sender_name}\n"
            f"📩 *Mensagem:* \"{message_text}\"\n\n"
            f"💡 *Sugestão de Resposta IA:*\n"
            f"_{reply_suggestion}_\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👉 *Para responder ao cliente agora:*\n"
            f"Responda: */r <sua mensagem>* ou *RESPONDER <sua mensagem>*"
        )
        return self.send_message(msg)

    def generate_hourly_report(self) -> str:
        """Gera o texto do relatório executivo periódico de 1 hora (Card 6.6)."""
        from datetime import datetime
        metrics = db.get_hourly_metrics()
        now_str = datetime.now().strftime("%H:%M")

        reasons_summary = ""
        if metrics["top_rejection_reasons"]:
            reasons_summary = "\n*🚫 Principais Filtros Aplicados:*\n"
            for reason, count in metrics["top_rejection_reasons"]:
                reasons_summary += f"  • {reason}: {count}x\n"

        report = (
            f"⏱️ *RELATÓRIO HORÁRIO ({now_str}) — BOT 99FREELAS*\n\n"
            f"🔍 *Varredura da Última Hora:*\n"
            f"• Projetos analisados: *{metrics['projects_scanned']}*\n"
            f"• Qualificados/Aprovados: *{metrics['projects_approved']}*\n"
            f"• Descartados pelo filtro: *{metrics['projects_rejected']}*\n"
            f"{reasons_summary}\n"
            f"⚡ *Conexões Diárias:* {metrics['connections_used_today']}/{settings.MAX_CONNECTIONS_PER_DAY} "
            f"(Restam: *{metrics['connections_remaining']}*)\n"
            f"📋 *Fila de Propostas:* *{metrics['pending_proposals']}* aguardando revisão\n\n"
            f"💡 _Para ver a fila, digite *FILA*. Para responder cliente, digite */r <msg>*._"
        )
        return report

    def send_hourly_report(self) -> bool:
        """Envia o relatório executivo periódico de 1 hora no WhatsApp (Card 6.6)."""
        report_text = self.generate_hourly_report()
        return self.send_message(report_text)

    def process_incoming_command(self, text: str, from_number: Optional[str] = None) -> str:
        """Processa comandos recebidos via Webhook do WhatsApp e retorna a resposta."""
        cmd = text.strip()
        cmd_lower = cmd.lower()

        # 1. Comando de Aprovação: SIM <id>, APROVAR <id>, ENVIAR <id>
        match_sim = re.match(r"^(?:sim|aprovar|enviar)\s+(\d+)$", cmd_lower)
        if match_sim:
            prop_id = int(match_sim.group(1))
            success, msg = db.approve_proposal(prop_id)
            if success:
                used = db.get_today_connections_used()
                remaining = max(0, settings.MAX_CONNECTIONS_PER_DAY - used)
                return (
                    f"🚀 *Proposta #{prop_id} Aprovada com Sucesso!*\n\n"
                    f"A proposta foi despachada para o 99Freelas.\n"
                    f"⚡ Conexões usadas hoje: *{used}/{settings.MAX_CONNECTIONS_PER_DAY}* (Restam: {remaining})"
                )
            else:
                return f"⚠️ *Não foi possível aprovar a proposta #{prop_id}:*\n{msg}"

        # 2. Comando de Rejeição: NAO <id>, RECUSAR <id>, DESCARTAR <id>
        match_nao = re.match(r"^(?:nao|não|recusar|descartar)\s+(\d+)$", cmd_lower)
        if match_nao:
            prop_id = int(match_nao.group(1))
            success, msg = db.reject_proposal(prop_id, reason="Rejeitado via WhatsApp")
            if success:
                return f"🗑️ *Proposta #{prop_id} descartada.*\nNenhuma conexão foi debitada."
            else:
                return f"⚠️ *Não foi possível descartar a proposta #{prop_id}:*\n{msg}"

        # 3. Consulta de Status / Conexões / Fila
        if cmd_lower in ("status", "fila", "conexoes", "conexões"):
            pending = db.get_pending_proposals()
            used = db.get_today_connections_used()
            remaining = max(0, settings.MAX_CONNECTIONS_PER_DAY - used)
            pending_count = len(pending)

            reply = (
                f"📊 *STATUS DA OPERAÇÃO*\n\n"
                f"⚡ *Conexões Hoje:* {used}/{settings.MAX_CONNECTIONS_PER_DAY} (Restam: {remaining})\n"
                f"📋 *Fila de Aprovação:* {pending_count} propostas pendentes\n"
            )
            if pending:
                reply += "\n*Propostas Aguardando Confirmação:*\n"
                for p in pending[:5]:
                    reply += f"• #{p['id']}: {p.get('project_title', 'Projeto')[:40]}... (R$ {p.get('price', 0):.0f})\n"
                reply += "\nPara aprovar, responda *SIM <id>*."
            return reply

        # 4. Ponte Bidirecional de Chat: /r <msg> ou RESPONDER <msg> (Card 6.5)
        match_reply = re.match(r"^(?:/r|responder)\s+(.+)$", cmd, re.IGNORECASE | re.DOTALL)
        if match_reply:
            reply_body = match_reply.group(1).strip()
            from bot_99freelas.chat.monitor import chat_monitor
            success, msg_result = chat_monitor.send_reply_to_freelas(reply_body)
            if success:
                return f"✅ *Mensagem enviada no chat do 99Freelas!*\n\n\"{reply_body}\""
            else:
                return f"⚠️ *Não foi possível enviar a mensagem:*\n{msg_result}"

        # 5. Relatório Periódico / Sob Demanda: RELATORIO (Card 6.6)
        if cmd_lower in ("relatorio", "relatório", "report"):
            return self.generate_hourly_report()

        # 6. Ajuda
        if cmd_lower in ("ajuda", "help", "comandos", "menu"):
            return (
                f"🤖 *COMANDOS DISPONÍVEIS NO WHATSAPP*\n\n"
                f"• *SIM <id>* - Aprova e despacha a proposta no 99Freelas.\n"
                f"• *NAO <id>* - Descarta a proposta sem gastar conexão.\n"
                f"• *STATUS* - Mostra conexões gastas e fila pendente.\n"
                f"• *FILA* - Lista as propostas aguardando sua revisão.\n"
                f"• */r <msg>* - Responde a última mensagem recebida no chat.\n"
                f"• *RELATORIO* - Gera o resumo operacional da última hora."
            )

        return (
            "Comando não reconhecido. Digite *AJUDA* para ver as opções, "
            "*SIM <id>* para aprovar uma proposta ou */r <msg>* para responder no chat."
        )


whatsapp_service = WhatsAppNotifier()

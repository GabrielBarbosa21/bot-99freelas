"""Módulo de submissão de propostas autenticadas no 99Freelas (Card 2.4)."""

import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional
from pydantic import BaseModel

from bot_99freelas.models.project import Project
from bot_99freelas.proposals.generator import GeneratedProposal
from bot_99freelas.crawler.session import session_manager
from bot_99freelas.storage.db import db

logger = logging.getLogger("ProposalSubmitter")


class SubmissionResult(BaseModel):
    """Resultado da tentativa de envio da proposta."""
    success: bool
    simulated: bool
    message: str
    response_code: Optional[int] = None


class ProposalSubmitter:
    """Responsável pelo despacho seguro e autenticado da proposta no 99Freelas."""

    def __init__(self, dry_run: bool = True):
        # Por padrão dry_run=True (modo seguro) para evitar disparos acidentais
        self.dry_run = dry_run
        self.session = session_manager

    def submit(self, project: Project, proposal: GeneratedProposal) -> SubmissionResult:
        """Envia a proposta para o projeto especificado."""
        # 1. Validação de conexões diárias disponíveis
        if not db.can_send_proposal_today():
            return SubmissionResult(
                success=False,
                simulated=self.dry_run,
                message="Limite diário de conexões esgotado.",
            )

        # 2. Modo Simulação Segura (Dry-Run)
        if self.dry_run:
            logger.info(
                f"[SIMULAÇÃO DRY-RUN] Proposta simulada com sucesso para '{project.title}' | "
                f"Valor: R$ {proposal.price:.2f} | Prazo: {proposal.delivery_days}d"
            )
            # Registra no banco local
            db.increment_today_connections()
            return SubmissionResult(
                success=True,
                simulated=True,
                message=f"Proposta simulada com sucesso no modo teste (Dry-run). Conexões usadas hoje: {db.get_today_connections_used()}",
                response_code=200,
            )

        # 3. Modo Live Autenticado
        cookie_header = self.session.get_cookie_header()
        if not cookie_header:
            return SubmissionResult(
                success=False,
                simulated=False,
                message="Nenhuma sessão ativa encontrada. Faça login ou adicione os cookies primeiro.",
            )

        endpoint = f"https://www.99freelas.com.br/project/proposal/submit"
        payload = {
            "project_id": project.id,
            "valor": proposal.price,
            "prazo": proposal.delivery_days,
            "descricao": proposal.text,
        }

        try:
            data = urllib.parse.urlencode(payload).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={
                    **self.session.DEFAULT_HEADERS,
                    "Cookie": cookie_header,
                    "Referer": project.url,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                status_code = resp.status
                if status_code in (200, 201, 302):
                    db.increment_today_connections()
                    return SubmissionResult(
                        success=True,
                        simulated=False,
                        message="Proposta enviada com sucesso no 99Freelas!",
                        response_code=status_code,
                    )
                return SubmissionResult(
                    success=False,
                    simulated=False,
                    message=f"Resposta inesperada do servidor: HTTP {status_code}",
                    response_code=status_code,
                )
        except Exception as e:
            logger.error(f"Erro ao submeter proposta: {e}")
            return SubmissionResult(
                success=False,
                simulated=False,
                message=f"Falha de rede ou sessão expirada: {e}",
            )


proposal_submitter = ProposalSubmitter(dry_run=True)

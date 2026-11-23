"""Modelos de dados para o módulo de conversação e atendimento inteligente."""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class MessageIntent(str, Enum):
    """Classificação da intenção da mensagem do cliente."""
    TECHNICAL_QUESTION = "technical_question"      # Dúvida técnica sobre como será feito
    PRICE_NEGOTIATION = "price_negotiation"        # Pedido de desconto / negociação de valor
    DEADLINE_NEGOTIATION = "deadline_negotiation"  # Negociação de prazo / urgência
    SCOPE_EXPANSION = "scope_expansion"            # Scope creep / pedido de funcionalidade extra
    CLOSING = "closing"                            # Intenção de fechar o projeto
    GENERAL_GREETING = "general_greeting"          # Saudação ou contato inicial
    UNKNOWN = "unknown"


class ChatMessage(BaseModel):
    """Mensagem individual trocada no chat do 99Freelas."""
    id: str
    project_id: str
    sender_name: str
    text: str
    timestamp: Optional[datetime] = None
    is_client: bool = True


class IntentAnalysis(BaseModel):
    """Resultado da análise de intenção da mensagem."""
    intent: MessageIntent
    confidence: float = Field(ge=0.0, le=1.0)
    is_scope_creep: bool = False
    detected_keywords: List[str] = Field(default_factory=list)
    suggested_reply: Optional[str] = None
    change_order_value: Optional[float] = None

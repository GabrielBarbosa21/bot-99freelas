"""Classificador de intenções para mensagens do cliente no 99Freelas."""

import re
from typing import List
from bot_99freelas.chat.models import MessageIntent, IntentAnalysis


class IntentClassifier:
    """Classifica a mensagem do cliente identificando a intenção e escopo extra."""

    PATTERNS = {
        MessageIntent.CLOSING: [
            r"como faço para contratar",
            r"vou aceitar a proposta",
            r"vamos fechar",
            r"podemos começar",
            r"quero fechar com você",
            r"como fazemos para iniciar",
            r"proposta aceita",
            r"gostei da sua proposta",
            r"quando você pode começar",
        ],
        MessageIntent.PRICE_NEGOTIATION: [
            r"faz por menos",
            r"dá pra fazer por",
            r"consegue um desconto",
            r"achei um pouco caro",
            r"meu orçamento é de",
            r"consegue melhorar o valor",
            r"tem como baixar",
            r"qual o menor valor",
        ],
        MessageIntent.DEADLINE_NEGOTIATION: [
            r"consegue entregar antes",
            r"preciso para hoje",
            r"tem como ser mais rápido",
            r"preciso com urgência",
            r"quanto tempo demora",
            r"consegue entregar até",
            r"qual o prazo final",
        ],
        MessageIntent.SCOPE_EXPANSION: [
            r"além disso",
            r"aproveitando que",
            r"também precisava",
            r"dá pra incluir",
            r"e se a gente fizesse",
            r"outra coisa que lembrei",
            r"você também faz",
            r"acrescentar",
            r"adicionar mais",
        ],
        MessageIntent.TECHNICAL_QUESTION: [
            r"como funciona",
            r"qual tecnologia",
            r"usa python",
            r"você tem experiência com",
            r"como você vai fazer",
            r"dá pra integrar com",
            r"funciona no linux",
            r"funciona no windows",
            r"e se a api cair",
            r"scraping",
            r"scraper",
            r"crawler",
            r"bot",
            r"python",
            r"api",
            r"automação",
            r"automacao",
            r"já fez",
            r"ja fez",
            r"tem exemplo",
            r"portfólio",
            r"portfolio",
            r"qual linguagem",
        ],
        MessageIntent.GENERAL_GREETING: [
            r"^olá",
            r"^oi",
            r"^bom dia",
            r"^boa tarde",
            r"^boa noite",
            r"tudo bem",
        ],
    }

    def classify(self, message_text: str) -> IntentAnalysis:
        text_lower = message_text.lower().strip()

        # 1. Checagem prioritária de Fechamento
        for pat in self.PATTERNS[MessageIntent.CLOSING]:
            if re.search(pat, text_lower):
                return IntentAnalysis(
                    intent=MessageIntent.CLOSING,
                    confidence=0.95,
                    detected_keywords=[pat],
                )

        # 2. Checagem de Escopo Inflado (no-free-work)
        for pat in self.PATTERNS[MessageIntent.SCOPE_EXPANSION]:
            if re.search(pat, text_lower):
                return IntentAnalysis(
                    intent=MessageIntent.SCOPE_EXPANSION,
                    confidence=0.90,
                    is_scope_creep=True,
                    detected_keywords=[pat],
                )

        # 3. Negociação de Preço
        for pat in self.PATTERNS[MessageIntent.PRICE_NEGOTIATION]:
            if re.search(pat, text_lower):
                return IntentAnalysis(
                    intent=MessageIntent.PRICE_NEGOTIATION,
                    confidence=0.90,
                    detected_keywords=[pat],
                )

        # 4. Negociação de Prazo
        for pat in self.PATTERNS[MessageIntent.DEADLINE_NEGOTIATION]:
            if re.search(pat, text_lower):
                return IntentAnalysis(
                    intent=MessageIntent.DEADLINE_NEGOTIATION,
                    confidence=0.90,
                    detected_keywords=[pat],
                )

        # 5. Dúvida Técnica
        for pat in self.PATTERNS[MessageIntent.TECHNICAL_QUESTION]:
            if re.search(pat, text_lower):
                return IntentAnalysis(
                    intent=MessageIntent.TECHNICAL_QUESTION,
                    confidence=0.85,
                    detected_keywords=[pat],
                )

        # 6. Saudação Geral
        for pat in self.PATTERNS[MessageIntent.GENERAL_GREETING]:
            if re.search(pat, text_lower):
                return IntentAnalysis(
                    intent=MessageIntent.GENERAL_GREETING,
                    confidence=0.80,
                    detected_keywords=[pat],
                )

        return IntentAnalysis(
            intent=MessageIntent.UNKNOWN,
            confidence=0.40,
            detected_keywords=[],
        )

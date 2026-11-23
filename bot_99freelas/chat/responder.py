"""Gerador de respostas em tempo real com proteção de escopo (no-free-work & customer-support)."""

from typing import Optional
from bot_99freelas.chat.models import MessageIntent, IntentAnalysis, ChatMessage
from bot_99freelas.models.project import Project


class ChatResponder:
    """Gera respostas consultivas, mantendo o valor e protegendo contra escopo abusivo."""

    def generate_reply(
        self,
        analysis: IntentAnalysis,
        message: ChatMessage,
        project: Optional[Project] = None,
        original_price: float = 280.0,
    ) -> str:
        intent = analysis.intent
        client_name = message.sender_name if message.sender_name and message.sender_name != "Cliente" else ""
        greeting = f"Olá, {client_name}!" if client_name else "Olá!"

        # 1. Fechamento de Projeto (Closing)
        if intent == MessageIntent.CLOSING:
            return (
                f"{greeting} Excelente notícia! Fico muito feliz em fecharmos essa parceria.\n\n"
                "Para iniciarmos oficialmente com total segurança para você, basta clicar em "
                "**'Aceitar Proposta'** aqui mesmo na página do projeto no 99Freelas.\n\n"
                "Assim que a plataforma liberar, daremos início imediato à primeira etapa de validação. "
                "Já estou com o ambiente preparado!"
            )

        # 2. Escopo Extra / Scope Creep (no-free-work)
        elif intent == MessageIntent.SCOPE_EXPANSION or analysis.is_scope_creep:
            estimated_extra = round(original_price * 0.4, 2)
            return (
                f"{greeting} Essa funcionalidade extra que você mencionou é uma ótima ideia e vai somar bastante ao projeto!\n\n"
                f"Como ela vai além do escopo inicial acordado, podemos incluí-la facilmente através de um adicional "
                f"de **R$ {estimated_extra:.2f}**, sem comprometer a qualidade nem atrasar o cronograma principal.\n\n"
                "Prefere que já façamos tudo junto nesse pacote completo ou prefere finalizar a entrega principal primeiro?"
            )

        # 3. Negociação de Preço (Holding Ground com Firmeza e Empatia)
        elif intent == MessageIntent.PRICE_NEGOTIATION:
            return (
                f"{greeting} Compreendo a sua busca pela melhor condição de orçamento!\n\n"
                f"O valor de R$ {original_price:.2f} já foi planejado com uma condição promocional muito especial, "
                "incluindo código limpo, testes de validação e 7 dias de garantia pós-entrega para sua total segurança.\n\n"
                "Se precisar reduzir o valor total, podemos modularizar a entrega retirando algum item secundário no momento. "
                "O que acha dessa abordagem?"
            )

        # 4. Negociação de Prazo / Urgência
        elif intent == MessageIntent.DEADLINE_NEGOTIATION:
            return (
                f"{greeting} Entendo perfeitamente a urgência da sua demanda!\n\n"
                "Tenho disponibilidade imediata para priorizar o seu desenvolvimento. "
                "Assim que a proposta for confirmada aqui no 99Freelas, focarei de forma dedicada para antecipar a entrega ao máximo.\n\n"
                "Podemos confirmar agora para eu já abrir o código?"
            )

        # 5. Dúvida Técnica
        elif intent == MessageIntent.TECHNICAL_QUESTION:
            return (
                f"{greeting} Excelente pergunta!\n\n"
                "A solução é construída com arquitetura limpa, documentação clara e validação de erros ponta a ponta. "
                "Isso garante que o sistema seja rápido, fácil de manter e seguro.\n\n"
                "Se houver algum ponto ou requisito específico do seu ambiente que queira alinhar, fico à disposição!"
            )

        # 6. Saudação Geral
        elif intent == MessageIntent.GENERAL_GREETING:
            return (
                f"{greeting} Tudo ótimo por aqui! Estou à disposição para tirar qualquer dúvida sobre a proposta "
                "e começarmos o seu projeto com tranquilidade."
            )

        # Fallback padrão consultivo
        return (
            f"{greeting} Mensagem recebida! Estou analisando os detalhes e já te respondo para alinharmos os próximos passos."
        )

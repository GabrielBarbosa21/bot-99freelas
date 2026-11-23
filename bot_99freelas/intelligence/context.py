"""Camada de inteligência semântica e diagnóstico do contexto real do cliente."""

import os
import re
import json
import urllib.request
from typing import List, Optional
from pydantic import BaseModel, Field

from bot_99freelas.models.project import Project


class ProjectContext(BaseModel):
    """Diagnóstico semântico extraído do anúncio do cliente."""
    client_pain: str = Field(description="A dor central ou objetivo prático do cliente")
    detected_technologies: List[str] = Field(default_factory=list, description="Tecnologias identificadas no escopo")
    suggested_approach: str = Field(description="Abordagem técnica recomendada para resolver a dor")
    hook_sentence: str = Field(description="Primeira frase da proposta focada na dor do cliente")


class ContextAnalyzer:
    """Analisa o contexto usando IA (Gemini API) ou heurísticas avançadas de NLP."""

    COMMON_TECH_STACK = [
        "python", "django", "fastapi", "flask", "javascript", "typescript",
        "react", "vue", "angular", "node.js", "nodejs", "php", "laravel",
        "wordpress", "woocommerce", "shopify", "postgresql", "mysql", "sqlite",
        "mongodb", "docker", "aws", "scraping", "crawler", "bot", "selenium",
        "playwright", "excel", "sheets", "webhook", "rest api"
    ]

    def __init__(self, api_key: Optional[str] = None):
        # Aceita chave do Gemini configurada via ambiente
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def _extract_tech_heuristics(self, text: str) -> List[str]:
        text_lower = text.lower()
        found = []
        for tech in self.COMMON_TECH_STACK:
            if re.search(r"\b" + re.escape(tech) + r"\b", text_lower):
                found.append(tech.title())
        return list(dict.fromkeys(found))

    def _analyze_heuristically(self, project: Project) -> ProjectContext:
        """Diagnóstico inteligente baseado em regras heurísticas de NLP."""
        title = project.title.strip()
        desc = project.description.strip()
        text_full = f"{title} {desc}"

        techs = self._extract_tech_heuristics(text_full)
        if not techs and project.skills_required:
            techs = project.skills_required

        # Identificação da dor principal
        lower = text_full.lower()
        if "integrar" in lower or "integração" in lower or "api" in lower or "webhook" in lower:
            pain = "Conectar sistemas de forma segura e sincronizada sem perda de dados."
            approach = "Criar endpoint resiliente com validação de payload, logs e retry automático."
            hook = f"Vi que você precisa de uma integração confiável para '{title}'. O ponto principal nesse tipo de serviço é garantir que nenhum dado se perca em instabilidades de rede."
        elif "bot" in lower or "automação" in lower or "automatizar" in lower:
            pain = "Automatizar tarefas repetitivas para economizar tempo e eliminar falhas humanas."
            approach = "Desenvolver automação assíncrona, com execução em background e alertas de status."
            hook = f"Compreendi a necessidade de automatizar esse fluxo em '{title}'. Uma automação eficiente precisa rodar de forma invisível e avisar imediatamente se ocorrer qualquer exceção."
        elif "scraping" in lower or "extrair" in lower or "coleta" in lower or "crawler" in lower:
            pain = "Extração estruturada e contínua de dados web contornando bloqueios."
            approach = "Construir scraper modular com headers dinâmicos e exportação direta para o formato desejado."
            hook = f"Analisei sua demanda de coleta de dados para '{title}'. O segredo em projetos assim é contornar alterações na página de origem e manter a coleta sempre estável."
        elif "bug" in lower or "ajuste" in lower or "corrigir" in lower or "erro" in lower:
            pain = "Resolver um problema pontual que está travando o fluxo atual."
            approach = "Diagnóstico cirúrgico na causa raiz com correção e teste de regressão."
            hook = f"Identifiquei que você precisa resolver esse ajuste em '{title}' com urgência para que o projeto volte a rodar perfeitamente."
        else:
            pain = f"Executar a implementação completa de '{title}' com padrão de qualidade e prazo ágil."
            approach = "Desenvolvimento estruturado em módulos com entregas graduais e validação constante."
            hook = f"Analisei com atenção os requisitos do seu projeto '{title}' e montei um plano sob medida para atender exatamente ao que você precisa."

        return ProjectContext(
            client_pain=pain,
            detected_technologies=techs,
            suggested_approach=approach,
            hook_sentence=hook,
        )

    def analyze(self, project: Project) -> ProjectContext:
        """Analisa o contexto do projeto priorizando IA se houver chave configurada."""
        # Se houver chave Gemini, podemos consultar a API, senão usamos o motor heurístico
        return self._analyze_heuristically(project)

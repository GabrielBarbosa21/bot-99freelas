"""Filtro de relevância semântica e descarte cirúrgico para preservação de conexões."""

import re
from typing import List, Optional
from pydantic import BaseModel, Field

from bot_99freelas.models.project import Project
from bot_99freelas.config import settings


class FilterResult(BaseModel):
    """Resultado da avaliação de relevância de um projeto."""
    accepted: bool
    score: float = Field(ge=0.0, le=100.0, description="Pontuação de adequação (0-100)")
    reasons: List[str] = Field(default_factory=list, description="Motivos de aprovação ou descarte")
    warnings: List[str] = Field(default_factory=list, description="Pontos de atenção")


class ProjectFilter:
    """Motor de filtragem e ranqueamento de projetos."""

    # Palavras-chave indicativas de spam, golpes ou demandas inviáveis
    SPAM_PATTERNS = [
        r"trabalhe em casa digitando",
        r"ganhe dinheiro assistindo",
        r"pirâmide",
        r"deposite para começar",
        r"chamar no whatsapp antes",
        r"contato direto por telegram",
        r"envie comprovante para liberar",
        r"trabalho fácil sem experiência ganhando \d+",
    ]

    # Palavras-chave de escopo abusivo vs orçamento baixo ("clone de uber por 50 reais")
    EXPENSIVE_SCOPE_KEYWORDS = [
        "uber", "ifood", "airbnb", "netflix", "rede social", 
        "marketplace", "shopee", "mercado livre", "clone",
        "aplicativo estilo", "sistema erp", "saas completo"
    ]

    def __init__(
        self,
        min_budget: Optional[float] = None,
        max_proposals: int = 15,
        min_client_hiring_rate: float = 20.0,
    ):
        self.min_budget = min_budget if min_budget is not None else settings.MIN_BUDGET
        self.max_proposals = max_proposals
        self.min_client_hiring_rate = min_client_hiring_rate

    def evaluate(self, project: Project) -> FilterResult:
        reasons: List[str] = []
        warnings: List[str] = []
        score = 70.0  # Base score inicial

        # 1. Checagem de Spam / Golpes
        text_to_check = f"{project.title} {project.description}".lower()
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text_to_check):
                return FilterResult(
                    accepted=False,
                    score=0.0,
                    reasons=[f"Descartado por suspeita de spam/golpe: padrão '{pattern}' detectado."]
                )

        # 2. Concorrência Excessiva (Preservação de Conexões)
        if project.proposals_count > self.max_proposals:
            return FilterResult(
                accepted=False,
                score=10.0,
                reasons=[f"Muitas propostas ({project.proposals_count} > {self.max_proposals}). Desperdício de conexão para perfil inicial."]
            )
        elif project.proposals_count <= 5:
            score += 15.0
            reasons.append("Poucas propostas concorrentes (vantagem de primeiro contato).")

        # 3. Análise de Orçamento
        budget = project.budget_average
        if budget is not None:
            if budget < self.min_budget:
                return FilterResult(
                    accepted=False,
                    score=20.0,
                    reasons=[f"Orçamento médio (R$ {budget:.2f}) abaixo do piso mínimo configurado (R$ {self.min_budget:.2f})."]
                )
            elif budget >= 500.0:
                score += 10.0
                reasons.append(f"Orçamento atrativo: R$ {budget:.2f}.")

            # Checar desproporção de escopo vs orçamento
            for complex_kw in self.EXPENSIVE_SCOPE_KEYWORDS:
                if complex_kw in text_to_check and budget < 400.0:
                    return FilterResult(
                        accepted=False,
                        score=15.0,
                        reasons=[f"Escopo complexo ('{complex_kw}') incompatível com orçamento irrealista de R$ {budget:.2f}."]
                    )
        else:
            warnings.append("Orçamento não especificado ou a combinar.")

        # 4. Histórico e Reputação do Cliente
        client = project.client
        if client.projects_published >= 3:
            if client.hiring_rate < self.min_client_hiring_rate:
                return FilterResult(
                    accepted=False,
                    score=25.0,
                    reasons=[f"Cliente publica muito mas raramente contrata (taxa: {client.hiring_rate}% < {self.min_client_hiring_rate}%)."]
                )
            else:
                score += 10.0
                reasons.append(f"Cliente confiável com histórico comprovado (taxa contratação: {client.hiring_rate}%).")
        elif client.projects_published == 0 or client.projects_published == 1:
            warnings.append("Cliente novo na plataforma (primeiro ou segundo projeto).")

        if client.rating is not None and client.rating < 3.5 and client.reviews_count >= 2:
            warnings.append(f"Avaliação média do cliente baixa ({client.rating:.1f}/5.0).")
            score -= 15.0

        # 5. Clareza da Descrição
        if len(project.description.strip()) < 40:
            warnings.append("Descrição muito vaga ou incompleta.")
            score -= 10.0

        # Normalização do Score (0 - 100)
        final_score = max(0.0, min(100.0, score))
        accepted = final_score >= 50.0

        if accepted and not reasons:
            reasons.append("Projeto alinhado com critérios de viabilidade e escopo.")

        return FilterResult(
            accepted=accepted,
            score=final_score,
            reasons=reasons,
            warnings=warnings
        )

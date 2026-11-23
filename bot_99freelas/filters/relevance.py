"""Filtro de relevância semântica e descarte cirúrgico para preservação de conexões (Filtro Sniper)."""

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
    """Motor de filtragem, calibração Sniper e ranqueamento de projetos."""

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

    # Descarte automático e silencioso de categorias fora de escopo (design puro, redação, vídeo, etc.)
    OUT_OF_SCOPE_PATTERNS = [
        r"\b(?:design de logo|logotipo|identidade visual|flyer|banner para redes sociais|cartão de visita)\b",
        r"\b(?:edição de vídeo|edicao de video|editor de vídeo|editor de reels|after effects|premiere)\b",
        r"\b(?:locução|locucao|locutor|gravação de voz|narração)\b",
        r"\b(?:traduzir texto|tradução de inglês|redação de artigos|redator de artigos|artigos para blog|redação seo)\b",
        r"\b(?:maquiagem|fotografia de produto|manicure)\b",
    ]

    # Stacks-alvo de altíssima afinidade (Python, Automação, APIs, Web Scraping, IA, Bots)
    TARGET_STACK_PATTERNS = [
        (r"\b(?:python|py)\b", "Python"),
        (r"\b(?:automação|automacao|automatizar|automation)\b", "Automação"),
        (r"\b(?:bot|bots|chatbot|telegram bot|whatsapp bot)\b", "Bots"),
        (r"\b(?:scraping|scraper|crawler|raspar|extrair dados|selenium|playwright)\b", "Web Scraping"),
        (r"\b(?:api|apis|rest|fastapi|flask|django|webhook|endpoint)\b", "APIs & Backend"),
        (r"\b(?:ia|inteligência artificial|inteligencia artificial|llm|chatgpt|openai|gemini)\b", "Inteligência Artificial"),
        (r"\b(?:script|scripts|planilha|excel|pandas|csv)\b", "Scripts & Dados"),
        (r"\b(?:javascript|typescript|node|react|fullstack)\b", "Desenvolvimento Web"),
    ]

    # Termos indicativos de entrega ágil (1 a 3 dias) para conquista rápida de avaliações 5 estrelas
    FAST_DELIVERY_PATTERNS = [
        r"\b(?:urgente|rápido|rapido|pequeno ajuste|ajuste simples|correção rápida|correcao rapida)\b",
        r"\b(?:script simples|1 dia|2 dias|3 dias|poucas horas|hoje mesmo|pequena alteração)\b",
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
        text_to_check = f"{project.title} {project.description}".lower()

        # 1. Checagem de Spam / Golpes
        for pattern in self.SPAM_PATTERNS:
            if re.search(pattern, text_to_check):
                return FilterResult(
                    accepted=False,
                    score=0.0,
                    reasons=[f"Descartado por suspeita de spam/golpe: padrão '{pattern}' detectado."]
                )

        # 2. Descarte Automático de Categorias Fora de Escopo (Design puro, tradução, vídeo, redação)
        # Só descarta se não contiver menção explícita a código/automação
        has_dev_indication = any(re.search(pat, text_to_check) for pat, _ in self.TARGET_STACK_PATTERNS[:6])
        if not has_dev_indication:
            for pat in self.OUT_OF_SCOPE_PATTERNS:
                if re.search(pat, text_to_check):
                    return FilterResult(
                        accepted=False,
                        score=0.0,
                        reasons=["Descartado: Demanda fora do escopo de desenvolvimento de software/automação."]
                    )

        score = 65.0  # Base inicial equilibrada

        # 3. Concorrência Excessiva (Preservação de Conexões)
        if project.proposals_count > self.max_proposals:
            return FilterResult(
                accepted=False,
                score=10.0,
                reasons=[f"Muitas propostas ({project.proposals_count} > {self.max_proposals}). Desperdício de conexão para perfil inicial."]
            )
        elif project.proposals_count <= 5:
            score += 15.0
            reasons.append("Poucas propostas concorrentes (vantagem de primeiro contato).")

        # 4. Análise de Orçamento
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

        # 5. Histórico e Reputação do Cliente
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

        # 6. Clareza da Descrição
        if len(project.description.strip()) < 40:
            warnings.append("Descrição muito vaga ou incompleta.")
            score -= 10.0

        # 🎯 7. Bônus Sniper para Stacks-Alvo de Desenvolvimento e Automação
        matched_stacks = []
        for pat, stack_name in self.TARGET_STACK_PATTERNS:
            if re.search(pat, text_to_check):
                matched_stacks.append(stack_name)

        if matched_stacks:
            # Bônus calibrado: 1 stack = +15, 2+ stacks = +25 pts
            affinity_bonus = 25.0 if len(matched_stacks) >= 2 else 15.0
            score += affinity_bonus
            reasons.append(f"🎯 Stack Sniper ({', '.join(matched_stacks)}): bônus de +{affinity_bonus:.0f} pts.")

        # ⚡ 8. Ponderação de Viabilidade de Entrega Ágil (Quick Win para 5 estrelas)
        for fast_pat in self.FAST_DELIVERY_PATTERNS:
            if re.search(fast_pat, text_to_check):
                score += 10.0
                reasons.append("⚡ Oportunidade de entrega ágil / Quick Win (+10 pts).")
                break

        # Normalização do Score (0 - 100)
        final_score = max(0.0, min(100.0, score))
        accepted = final_score >= 50.0

        # 🤖 9. Refinamento e Validação Crítica com IA Gemini (se configurado)
        try:
            from bot_99freelas.intelligence.gemini import gemini_service
            if gemini_service.is_configured() and final_score >= 35.0:
                ai_eval = gemini_service.evaluate_project(project)
                if ai_eval and isinstance(ai_eval, dict):
                    ai_score = float(ai_eval.get("score", final_score))
                    ai_reason = ai_eval.get("reason", "")
                    ai_accepted = bool(ai_eval.get("accepted", accepted))
                    
                    # Calibra com a IA
                    final_score = round((final_score * 0.4) + (ai_score * 0.6), 1)
                    accepted = ai_accepted and (final_score >= 50.0)

                    if ai_reason:
                        if accepted:
                            reasons.append(f"🤖 IA Gemini ({ai_score:.0f} pts): {ai_reason}")
                        else:
                            warnings.append(f"🤖 IA Gemini rejeitou: {ai_reason}")
                    
                    tech_angle = ai_eval.get("technical_angle")
                    if tech_angle:
                        reasons.append(f"💡 Ângulo IA sugerido: {tech_angle}")
        except Exception:
            pass

        if accepted and final_score >= 90.0:
            reasons.append("🔥 Prioridade Máxima Sniper: Score 90+!")
        elif accepted and not reasons:
            reasons.append("Projeto alinhado com critérios de viabilidade e escopo.")

        return FilterResult(
            accepted=accepted,
            score=final_score,
            reasons=reasons,
            warnings=warnings
        )


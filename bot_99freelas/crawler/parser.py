"""Parser de HTML e feeds de projetos do 99Freelas."""

import re
from html import unescape
from typing import List, Optional
from bot_99freelas.models.project import Project, ClientProfile, BudgetType


class FreelasParser:
    """Extrai projetos reais a partir do HTML do 99Freelas."""

    BASE_URL = "https://www.99freelas.com.br"

    @classmethod
    def parse_budget_string(cls, budget_str: str) -> tuple[Optional[float], Optional[float]]:
        """Extrai valores numéricos de expressões como 'R$ 200 - R$ 500' ou 'Menos de R$ 500'."""
        if not budget_str:
            return 200.0, 500.0

        matches = re.findall(r"R\$\s*([\d\.\,]+)", budget_str)
        numbers = []
        for m in matches:
            clean = m.replace(".", "").replace(",", ".")
            try:
                numbers.append(float(clean))
            except ValueError:
                pass

        if len(numbers) >= 2:
            return min(numbers[0], numbers[1]), max(numbers[0], numbers[1])
        elif len(numbers) == 1:
            val = numbers[0]
            if "menos de" in budget_str.lower() or "até" in budget_str.lower():
                return 100.0, val
            return val, val
        return 200.0, 500.0

    @classmethod
    def parse_project_block(cls, b: str) -> Optional[Project]:
        """Extrai um projeto a partir do bloco HTML do item."""
        id_m = re.search(r'data-id=["\'](\d+)["\']', b)
        link_m = re.search(r'<h[1-4][^>]*class=["\']title["\'][^>]*>\s*<a href=["\']([^"\']+)["\']>([^<]+)</a>', b)
        if not link_m:
            link_m = re.search(r'href=["\'](/project/[^"\']+|/projeto/[^"\']+)["\'][^>]*>([^<]+)</a>', b)

        if not link_m:
            return None

        rel_url = link_m.group(1).split("?")[0]
        title = unescape(link_m.group(2).strip())
        proj_id = id_m.group(1) if id_m else rel_url.split("/")[-1]

        prop_m = re.search(r'Propostas:\s*<b>(\d+)</b>|(\d+)\s+proposta', b, re.IGNORECASE)
        proposals_count = int(prop_m.group(1) or prop_m.group(2)) if prop_m else 0

        desc_m = re.search(
            r'class=["\']item-text description formatted-text["\'][^>]*data-content=["\']([^"\']+)["\']',
            b,
        )
        if desc_m:
            raw_desc = desc_m.group(1).replace("<br/>", "\n").replace("<br>", "\n")
            desc = unescape(re.sub(r"<[^>]+>", "", raw_desc).strip())
        else:
            desc_text_m = re.search(r'class=["\']item-text description formatted-text["\'][^>]*>(.*?)</div>', b, re.DOTALL)
            if not desc_text_m:
                desc_text_m = re.search(r'class=["\']description["\'][^>]*>(.*?)</div>', b, re.DOTALL)
            desc = unescape(re.sub(r"<[^>]+>", "", desc_text_m.group(1)).strip()) if desc_text_m else title

        rating_m = re.search(r'data-score=["\']([\d\.]+)["\']', b)
        rating = float(rating_m.group(1)) if rating_m else None
        reviews_m = re.search(r'\((\d+)\s+avaliaç', b, re.IGNORECASE)
        reviews_count = int(reviews_m.group(1)) if reviews_m else 0

        client_name_m = re.search(r'class=["\'][^"\']*(?:client|cliente|author)[^"\']*["\'][^>]*>(.*?)<', b, re.DOTALL)
        client_name = unescape(client_name_m.group(1)).strip() if client_name_m else "Cliente"

        b_min, b_max = cls.parse_budget_string(b)
        url = f"{cls.BASE_URL}{rel_url}" if not rel_url.startswith("http") else rel_url

        return Project(
            id=proj_id,
            url=url,
            title=title,
            description=desc,
            category="Web, Mobile e Software",
            budget_min=b_min,
            budget_max=b_max,
            proposals_count=proposals_count,
            client=ClientProfile(
                name=client_name,
                rating=rating,
                reviews_count=reviews_count,
            ),
        )

    @classmethod
    def parse_projects_page(cls, html_content: str) -> List[Project]:
        """Varre a listagem HTML do 99Freelas e extrai todos os projetos detalhados."""
        blocks = re.split(r'<li[^>]*class=["\'][^"\']*result-item[^"\']*["\']', html_content)[1:]
        projects: List[Project] = []

        for b in blocks:
            proj = cls.parse_project_block(b)
            if proj:
                projects.append(proj)

        return projects

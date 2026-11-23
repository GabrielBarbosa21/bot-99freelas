"""Parser de HTML e feeds de projetos do 99Freelas."""

import re
from html import unescape
from typing import List, Optional
from bot_99freelas.models.project import Project, ClientProfile, BudgetType


class FreelasParser:
    """Extrai projetos a partir do HTML ou endpoints da listagem do 99Freelas."""

    BASE_URL = "https://www.99freelas.com.br"

    @classmethod
    def parse_budget_string(cls, budget_str: str) -> tuple[Optional[float], Optional[float]]:
        """Extrai valores numéricos de expressões como 'R$ 200 - R$ 500' ou 'Menos de R$ 500'."""
        if not budget_str:
            return None, None

        # Procura padrões monetários (ex: 250,00 ou 500)
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
        return None, None

    @classmethod
    def parse_project_block(cls, item_html: str) -> Optional[Project]:
        """Extrai os dados de um card de projeto individual no 99Freelas."""
        # Extração de Link e ID
        link_match = re.search(r'href=["\'](/projeto/[^"\']+)["\']', item_html)
        if not link_match:
            # Fallback para url completa ou id
            link_match = re.search(r'href=["\'](https?://[^"\']*/projeto/[^"\']+)["\']', item_html)

        if not link_match:
            return None

        rel_url = link_match.group(1)
        url = rel_url if rel_url.startswith("http") else f"{cls.BASE_URL}{rel_url}"

        # ID extraído da URL
        id_match = re.search(r"/projeto/([^/?#]+)", url)
        project_id = id_match.group(1) if id_match else f"p-{abs(hash(url))}"

        # Título
        title_match = re.search(r'<h[1-4][^>]*>(.*?)</h[1-4]>', item_html, re.DOTALL)
        if not title_match:
            title_match = re.search(r'class=["\'][^"\']*title[^"\']*["\'][^>]*>(.*?)<', item_html, re.DOTALL)
        title = unescape(re.sub(r"<[^>]+>", "", title_match.group(1)).strip()) if title_match else "Projeto sem título"

        # Descrição
        desc_match = re.search(r'class=["\'][^"\']*(?:description|descricao|resumo)[^"\']*["\'][^>]*>(.*?)</div>', item_html, re.DOTALL)
        desc = unescape(re.sub(r"<[^>]+>", "", desc_match.group(1)).strip()) if desc_match else title

        # Orçamento
        budget_min, budget_max = cls.parse_budget_string(item_html)

        # Propostas
        prop_match = re.search(r"(\d+)\s+proposta", item_html, re.IGNORECASE)
        proposals_count = int(prop_match.group(1)) if prop_match else 0

        # Cliente
        client_name_match = re.search(r'class=["\'][^"\']*(?:client|cliente|author)[^"\']*["\'][^>]*>(.*?)<', item_html, re.DOTALL)
        client_name = unescape(client_name_match.group(1)).strip() if client_name_match else "Cliente"

        client = ClientProfile(name=client_name)

        return Project(
            id=project_id,
            url=url,
            title=title,
            description=desc,
            category="Web & Software",
            budget_min=budget_min,
            budget_max=budget_max,
            proposals_count=proposals_count,
            client=client,
        )

    @classmethod
    def parse_projects_page(cls, html_content: str) -> List[Project]:
        """Varre a página de listagem e retorna todos os projetos identificados."""
        # Divide por blocos comuns de itens na lista do 99Freelas
        items = re.findall(r'(<(?:li|div)[^>]*class=["\'][^"\']*(?:project-item|item|result-item)[^"\']*["\'].*?</(?:li|div)>)', html_content, re.DOTALL)
        projects = []
        if items:
            for item in items:
                proj = cls.parse_project_block(item)
                if proj:
                    projects.append(proj)
        else:
            # Fallback por tags de links de projetos
            links = re.findall(r'(<a[^>]*href=["\']/projeto/[^"\']+["\'].*?</a>)', html_content, re.DOTALL)
            for link in links:
                proj = cls.parse_project_block(link)
                if proj:
                    projects.append(proj)

        return projects

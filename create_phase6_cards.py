import urllib.request
import json
from bot_99freelas.config import settings

headers = {
    "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "Bot-99Freelas",
    "Content-Type": "application/json",
}

cards = [
    {
        "title": "🛡️ [Fase 6] Card 6.1: Autenticação e Segurança do Painel Web",
        "body": (
            "### 🎯 Objetivo\n"
            "Proteger o painel de controle na nuvem contra acessos não autorizados, implementando tela de login seguro, "
            "sessões criptografadas e proteção em todos os endpoints da API.\n\n"
            "### 📋 Checklist de Implementação\n"
            "- [ ] Definir credenciais seguras no `.env` (`ADMIN_USERNAME` e `ADMIN_PASSWORD`).\n"
            "- [ ] Criar tela de login minimalista e moderna (`/login`) com logout (`/logout`).\n"
            "- [ ] Middleware de autenticação protegendo todas as rotas e APIs do dashboard.\n"
            "- [ ] Proteção contra força bruta (rate limiting nas tentativas de login).\n"
            "- [ ] Cookies de sessão seguros (`HttpOnly`, `SameSite=Lax`)."
        ),
    },
    {
        "title": "🎨 [Fase 6] Card 6.2: Redesign Visual Minimalista da UI (Dashboard Clean)",
        "body": (
            "### 🎯 Objetivo\n"
            "Eliminar a poluição visual e o excesso de texto do painel, adotando um visual limpo, moderno e direto no estilo SaaS Dashboard.\n\n"
            "### 📋 Checklist de Implementação\n"
            "- [ ] Redesenhar layout com tipografia moderna, espaçamentos consistentes e menos verbosidade.\n"
            "- [ ] Cards de métricas diretos: Conexões gastas/restantes hoje, Propostas pendentes, Respostas recebidas.\n"
            "- [ ] Seção destacada de **Fila de Aprovação**: visualização clara do briefing + proposta da IA antes do envio.\n"
            "- [ ] Interface limpa de visualização do chat com clientes."
        ),
    },
    {
        "title": "🎯 [Fase 6] Card 6.3: Controle Granular de Varredura e Filtros de Busca",
        "body": (
            "### 🎯 Objetivo\n"
            "Permitir controle total sobre exatamente o que está sendo buscado e filtrado no 99Freelas, tanto pelo painel quanto via configurações.\n\n"
            "### 📋 Checklist de Implementação\n"
            "- [ ] Gestor de palavras-chave positivas prioritárias (Python, APIs, Web Scraping, Bots, Automação).\n"
            "- [ ] Blacklist de palavras-chave negativas (TCC, trabalhos acadêmicos, digitação, WordPress).\n"
            "- [ ] Configuração de categorias e subcategorias ativas no monitor.\n"
            "- [ ] Parâmetros de concorrência máxima e teto/piso de orçamento ajustáveis.\n"
            "- [ ] Feed resumido em tempo real das varreduras com motivo objetivo de cada descarte."
        ),
    },
    {
        "title": "📱 [Fase 6] Card 6.4: WhatsApp Copilot — Aprovação de Conexões e Propostas",
        "body": (
            "### 🎯 Objetivo\n"
            "Impedir disparos automáticos sem leitura prévia: enviar projetos qualificados e propostas geradas pela IA diretamente no WhatsApp do usuário para confirmação antes de gastar conexões.\n\n"
            "### 📋 Checklist de Implementação\n"
            "- [ ] Integração com gateway de WhatsApp (Evolution API / Z-API / Baileys webhook).\n"
            "- [ ] Formatação de mensagem com Resumo do Projeto, Orçamento, Concorrência e Proposta sugerida pela IA.\n"
            "- [ ] Comando de aprovação no WhatsApp (ex: `SIM <id>` ou botão interativo) para disparar o envio oficial no 99Freelas.\n"
            "- [ ] Trava rígida: nenhuma conexão é gasta sem o aval explícito do usuário."
        ),
    },
    {
        "title": "💬 [Fase 6] Card 6.5: Ponte Bidirecional WhatsApp ➔ Chat do 99Freelas",
        "body": (
            "### 🎯 Objetivo\n"
            "Permitir atendimento ágil aos clientes do 99Freelas diretamente pelo WhatsApp, com suporte e sugestões da IA.\n\n"
            "### 📋 Checklist de Implementação\n"
            "- [ ] Notificação instantânea no WhatsApp quando o cliente enviar mensagem no chat do 99Freelas.\n"
            "- [ ] Sugestão de resposta consultiva gerada pelo Gemini mantendo a salvaguarda No-Free-Work.\n"
            "- [ ] Capacidade de responder pelo WhatsApp (`/r <mensagem>`) com envio automático de volta para o chat do 99Freelas."
        ),
    },
    {
        "title": "⏱️ [Fase 6] Card 6.6: Relatório Periódico de 1 Hora no WhatsApp",
        "body": (
            "### 🎯 Objetivo\n"
            "Enviar automaticamente a cada 60 minutos um relatório executivo das operações para acompanhamento transparente.\n\n"
            "### 📋 Checklist de Implementação\n"
            "- [ ] Scheduler periódico a cada 1 hora no monitor.\n"
            "- [ ] Compilação de métricas da última hora: Projetos varridos, Descartes por motivo, Oportunidades encontradas.\n"
            "- [ ] Resumo de conexões restantes e propostas aguardando aprovação.\n"
            "- [ ] Envio formatado e conciso no WhatsApp do usuário."
        ),
    },
]

url = f"https://api.github.com/repos/{settings.GITHUB_REPO}/issues"
created = []

for c in cards:
    req = urllib.request.Request(url, data=json.dumps(c).encode("utf-8"), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
            num = data.get("number")
            title = data.get("title")
            created.append((num, title))
            print(f"✅ Card criado no GitHub: #{num} - {title}")
    except Exception as e:
        print(f"❌ Erro ao criar card '{c['title']}': {e}")

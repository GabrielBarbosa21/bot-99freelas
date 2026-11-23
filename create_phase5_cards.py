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
        "title": "🎛️ [Fase 5] Card 5.1: Unificação do Monitor 24h no Painel Web",
        "body": (
            "### 🎯 Objetivo\n"
            "Unificar o monitor assíncrono diretamente dentro da interface web do painel (`http://localhost:5000`), "
            "eliminando a necessidade de manter dois terminais separados abertos.\n\n"
            "### 📋 Checklist de Implementação\n"
            "- [ ] Integrar o thread do monitor em background no servidor do painel web.\n"
            "- [ ] Criar endpoints `/api/monitor/start`, `/api/monitor/stop` e `/api/monitor/status`.\n"
            "- [ ] Adicionar botão de ligar/desligar com indicador visual (🟢 Ativo 24h / 🔴 Pausado) no topo do Painel.\n"
            "- [ ] Transmitir logs e eventos de novas varreduras ao vivo diretamente na interface web."
        ),
    },
    {
        "title": "🎯 [Fase 5] Card 5.2: Filtro Sniper para Oportunidades de Desenvolvimento",
        "body": (
            "### 🎯 Objetivo\n"
            "Calibrar o motor de relevância semântica para priorizar cirurgicamente os melhores projetos de "
            "desenvolvimento de software, automações, bots, APIs e IA com pontuação máxima (Score 95+).\n\n"
            "### 📋 Checklist de Implementação\n"
            "- [ ] Configurar bônus de afinidade para stacks-alvo: Python, Automação, APIs, Web Scraping, IA, Bots.\n"
            "- [ ] Descarte automático e silencioso de categorias fora de escopo (design puro, tradução, vídeo).\n"
            "- [ ] Ponderação de viabilidade de entrega ágil (1 a 3 dias) para conquista rápida de avaliações 5 estrelas."
        ),
    },
    {
        "title": "🛡️ [Fase 5] Card 5.3: Motor de Resiliência e Auto-Recuperação 24 Horas",
        "body": (
            "### 🎯 Objetivo\n"
            "Garantir operação contínua 24h estável e ininterrupta, tratando quedas de internet, timeouts e sessões.\n\n"
            "### 📋 Checklist de Implementação\n"
            "- [ ] Tratamento de falhas de rede com retentativas automáticas e backoff exponencial.\n"
            "- [ ] Validação periódica da validade da sessão com alerta caso precise renovar cookies.\n"
            "- [ ] Sistema de rotação de logs em arquivo para diagnóstico contínuo de longo prazo."
        ),
    },
    {
        "title": "🚀 [Fase 5] Card 5.4: Inicialização Automática e Modo Silencioso no Windows",
        "body": (
            "### 🎯 Objetivo\n"
            "Permitir que o bot rode de forma silenciosa em segundo plano 24/7 e inicie automaticamente junto com o Windows.\n\n"
            "### 📋 Checklist de Implementação\n"
            "- [ ] Script silencioso em VBScript / PowerShell para rodar sem janela aberta de terminal.\n"
            "- [ ] Script de instalação no `shell:startup` para autoinício no boot do computador.\n"
            "- [ ] Script de parada segura (`parar_bot.bat`)."
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

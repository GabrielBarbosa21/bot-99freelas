"""Templates HTML modernos e minimalistas para o Dashboard Web (Card 6.2)."""

DASHBOARD_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot 99Freelas | Painel Operacional</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .font-mono-code { font-family: 'JetBrains Mono', monospace; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #090d16; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #334155; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased">
    <!-- Header Minimalista -->
    <header class="border-b border-slate-800/80 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="flex items-center space-x-2">
                    <span class="text-xl">⚡</span>
                    <span class="font-bold text-base text-white tracking-tight">Bot 99Freelas</span>
                </div>

                <!-- Status Pills -->
                <div class="hidden sm:flex items-center space-x-2 pl-2 border-l border-slate-800">
                    <span id="badge-monitor" class="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
                        Carregando...
                    </span>
                    <button onclick="openLoginModal()" id="badge-session" class="px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-800 hover:bg-slate-700 text-slate-400 border border-slate-700 transition cursor-pointer">
                        🔑 Sessão
                    </button>
                    <button onclick="openAIModal()" id="badge-ai" class="px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/20 transition cursor-pointer">
                        ✨ Gemini IA
                    </button>
                </div>
            </div>

            <!-- Ações do Topo -->
            <div class="flex items-center space-x-2">
                <button id="btn-toggle-monitor" onclick="toggleMonitor()" class="text-xs font-semibold px-3 py-1.5 rounded-lg border transition shadow-sm bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-500/30 flex items-center space-x-1.5">
                    <span id="icon-monitor">▶</span>
                    <span id="label-monitor">Iniciar Monitor</span>
                </button>
                <button onclick="fetchData()" title="Atualizar dados" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1.5 rounded-lg border border-slate-700 transition">
                    🔄
                </button>
                <button onclick="openAIModal()" title="Configurações IA" class="text-xs bg-purple-950/60 hover:bg-purple-900/60 text-purple-300 px-2.5 py-1.5 rounded-lg border border-purple-800/40 transition">
                    🤖
                </button>
                <button onclick="openLoginModal()" title="Conta 99Freelas" class="text-xs bg-indigo-950/60 hover:bg-indigo-900/60 text-indigo-300 px-2.5 py-1.5 rounded-lg border border-indigo-800/40 transition">
                    🔑
                </button>
                <a href="/logout" title="Sair do painel" class="text-xs bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 px-2.5 py-1.5 rounded-lg border border-slate-700 transition">
                    🚪 Sair
                </a>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6 flex-1 w-full">
        <!-- Banner de Sessão Desconectada (apenas se expirada) -->
        <div id="session-alert-banner" class="hidden bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 flex items-center justify-between text-xs text-amber-200">
            <div class="flex items-center space-x-2">
                <span class="text-base">⚠️</span>
                <span><strong>Sessão desconectada:</strong> Faça login para despachar propostas e monitorar oportunidades com precisão.</span>
            </div>
            <button onclick="openLoginModal()" class="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold px-3 py-1 rounded-lg transition text-[11px]">
                Conectar Conta
            </button>
        </div>

        <!-- 4 KPIs Diretos & Concisos -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            <div class="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                <div class="flex items-center justify-between text-xs text-slate-400">
                    <span>Conexões Diárias</span>
                    <span>⚡ Limite: 3</span>
                </div>
                <div class="mt-2 flex items-baseline space-x-2">
                    <span id="kpi-connections-used" class="text-2xl font-bold text-white">0</span>
                    <span class="text-xs text-slate-400">/ 3 usadas hoje</span>
                </div>
                <div class="mt-2 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div id="kpi-connections-bar" class="bg-indigo-500 h-1.5 rounded-full transition-all duration-500" style="width: 0%"></div>
                </div>
            </div>

            <div class="bg-slate-900/80 border border-slate-800 p-4 rounded-xl relative overflow-hidden">
                <div class="text-xs text-slate-400 flex items-center justify-between">
                    <span>Fila de Aprovação</span>
                    <span id="kpi-pending-pulse" class="hidden w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                </div>
                <div class="mt-2 flex items-baseline space-x-2">
                    <span id="kpi-pending-count" class="text-2xl font-bold text-amber-300">0</span>
                    <span class="text-xs text-slate-400">aguardando revisão</span>
                </div>
                <div class="text-[11px] text-slate-500 mt-1.5">Human-in-the-Loop Ativo</div>
            </div>

            <div class="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                <div class="text-xs text-slate-400">Oportunidades Vistas</div>
                <div class="mt-2 flex items-baseline space-x-2">
                    <span id="kpi-projects-count" class="text-2xl font-bold text-white">0</span>
                    <span id="kpi-conversion-rate" class="text-xs text-emerald-400 font-medium">0% aprovados</span>
                </div>
                <div class="text-[11px] text-slate-500 mt-1.5">Filtro Sniper Ativo</div>
            </div>

            <div class="bg-slate-900/80 border border-slate-800 p-4 rounded-xl">
                <div class="text-xs text-slate-400">Faturamento Total & Pipeline</div>
                <div class="mt-2 flex items-baseline space-x-2">
                    <span id="kpi-revenue" class="text-2xl font-bold text-emerald-400">R$ 0</span>
                </div>
                <div id="kpi-pipeline" class="text-[11px] text-slate-500 mt-1.5">Pipeline: R$ 0,00</div>
            </div>
        </div>

        <!-- Navegação por Abas (Clean Tabs) -->
        <div class="border-b border-slate-800/80 flex items-center space-x-2 text-xs font-semibold overflow-x-auto pb-px">
            <button onclick="switchTab('tab-proposals')" id="nav-tab-proposals" class="px-4 py-2.5 border-b-2 border-indigo-500 text-white flex items-center space-x-2 transition">
                <span>📋 Fila de Aprovação</span>
                <span id="tab-proposals-badge" class="bg-amber-500/20 text-amber-300 text-[10px] px-1.5 py-0.2 rounded-full font-bold">0</span>
            </button>
            <button onclick="switchTab('tab-feed')" id="nav-tab-feed" class="px-4 py-2.5 border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition flex items-center space-x-1.5">
                <span>📡 Feed de Projetos</span>
            </button>
            <button onclick="switchTab('tab-kanban')" id="nav-tab-kanban" class="px-4 py-2.5 border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition flex items-center space-x-1.5">
                <span>📊 Quadro de Tarefas</span>
            </button>
            <button onclick="switchTab('tab-logs')" id="nav-tab-logs" class="px-4 py-2.5 border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition flex items-center space-x-1.5">
                <span>🖥️ Terminal de Logs</span>
            </button>
            <button onclick="switchTab('tab-chat')" id="nav-tab-chat" class="px-4 py-2.5 border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition flex items-center space-x-1.5">
                <span>💬 Teste Chat IA</span>
            </button>
        </div>

        <!-- Conteúdo das Abas -->

        <!-- ABA 1: FILA DE APROVAÇÃO (HUMAN-IN-THE-LOOP) -->
        <section id="tab-proposals" class="tab-content space-y-4">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-sm font-bold text-white">Propostas Aguardando Aprovação</h2>
                    <p class="text-xs text-slate-400">Propostas elaboradas com IA prontas para leitura. Nenhuma conexão é gasta sem sua confirmação.</p>
                </div>
                <button onclick="fetchPendingProposals()" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition">
                    Atualizar Fila
                </button>
            </div>

            <!-- Lista de Propostas Pendentes -->
            <div id="pending-proposals-list" class="space-y-3">
                <div class="bg-slate-900/60 border border-slate-800/80 rounded-xl p-8 text-center text-slate-500 text-xs">
                    <span class="text-2xl block mb-2">☕</span>
                    Tudo limpo! Nenhuma proposta pendente no momento. Quando o monitor identificar oportunidades com score alto, elas aparecerão aqui.
                </div>
            </div>
        </section>

        <!-- ABA 2: FEED DO 99FREELAS -->
        <section id="tab-feed" class="tab-content hidden space-y-4">
            <div class="flex items-center justify-between flex-wrap gap-2">
                <div>
                    <h2 class="text-sm font-bold text-white">Projetos Identificados</h2>
                    <p class="text-xs text-slate-400">Histórico de varreduras com pontuação semântica de relevância.</p>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="filterProjectsTable('all')" class="feed-filter-btn px-2.5 py-1 rounded-md text-xs bg-slate-800 text-white font-medium">Todos</button>
                    <button onclick="filterProjectsTable('approved')" class="feed-filter-btn px-2.5 py-1 rounded-md text-xs text-slate-400 hover:text-white">Aprovados</button>
                    <button onclick="filterProjectsTable('rejected')" class="feed-filter-btn px-2.5 py-1 rounded-md text-xs text-slate-400 hover:text-white">Descartados</button>
                </div>
            </div>

            <div class="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs">
                        <thead class="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800">
                            <tr>
                                <th class="px-4 py-3">Projeto</th>
                                <th class="px-4 py-3">Concorrência</th>
                                <th class="px-4 py-3">Score IA</th>
                                <th class="px-4 py-3">Status</th>
                                <th class="px-4 py-3 text-right">Ação</th>
                            </tr>
                        </thead>
                        <tbody id="projects-table" class="divide-y divide-slate-800/60 text-slate-300">
                            <tr>
                                <td colspan="5" class="px-4 py-6 text-center text-slate-500">Aguardando registros do monitor...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- ABA 3: QUADRO KANBAN -->
        <section id="tab-kanban" class="tab-content hidden space-y-4">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-sm font-bold text-white">Quadro de Execução e Tarefas (Kanban)</h2>
                    <p class="text-xs text-slate-400">Acompanhamento ágil das entregas de projetos aceitos.</p>
                </div>
                <button onclick="promptNewTask()" class="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg transition font-semibold">
                    + Nova Tarefa
                </button>
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-3">
                    <div class="flex items-center justify-between text-xs font-semibold text-slate-300 mb-3 pb-2 border-b border-slate-800">
                        <span>A Fazer</span>
                        <span id="badge-todo" class="bg-slate-800 px-2 py-0.5 rounded text-[10px]">0</span>
                    </div>
                    <div id="col-todo" class="space-y-2 min-h-[200px]"></div>
                </div>

                <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-3">
                    <div class="flex items-center justify-between text-xs font-semibold text-sky-300 mb-3 pb-2 border-b border-slate-800">
                        <span>Em Andamento</span>
                        <span id="badge-inprogress" class="bg-sky-950/60 text-sky-400 px-2 py-0.5 rounded text-[10px]">0</span>
                    </div>
                    <div id="col-inprogress" class="space-y-2 min-h-[200px]"></div>
                </div>

                <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-3">
                    <div class="flex items-center justify-between text-xs font-semibold text-purple-300 mb-3 pb-2 border-b border-slate-800">
                        <span>Revisão</span>
                        <span id="badge-review" class="bg-purple-950/60 text-purple-400 px-2 py-0.5 rounded text-[10px]">0</span>
                    </div>
                    <div id="col-review" class="space-y-2 min-h-[200px]"></div>
                </div>

                <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-3">
                    <div class="flex items-center justify-between text-xs font-semibold text-emerald-300 mb-3 pb-2 border-b border-slate-800">
                        <span>Concluído</span>
                        <span id="badge-done" class="bg-emerald-950/60 text-emerald-400 px-2 py-0.5 rounded text-[10px]">0</span>
                    </div>
                    <div id="col-done" class="space-y-2 min-h-[200px]"></div>
                </div>
            </div>
        </section>

        <!-- ABA 4: TERMINAL DE LOGS -->
        <section id="tab-logs" class="tab-content hidden space-y-3">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-sm font-bold text-white">Terminal de Logs ao Vivo</h2>
                    <p class="text-xs text-slate-400">Eventos de rede, scraping e triagem em tempo real.</p>
                </div>
                <div class="flex items-center space-x-3 text-xs">
                    <label class="flex items-center space-x-1.5 text-slate-400 cursor-pointer">
                        <input type="checkbox" id="chk-autoscroll" checked class="rounded bg-slate-900 border-slate-700">
                        <span>Auto-scroll</span>
                    </label>
                    <button onclick="clearTerminalLogs()" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded border border-slate-700 transition">
                        Limpar
                    </button>
                </div>
            </div>

            <div class="bg-slate-950 border border-slate-800/80 rounded-xl p-4 font-mono-code text-xs h-[420px] overflow-y-auto space-y-1 shadow-inner" id="terminal-console">
                <div class="text-slate-500">// Terminal pronto. Logs do monitor aparecerão aqui...</div>
            </div>
        </section>

        <!-- ABA 5: CHAT IA PLAYGROUND -->
        <section id="tab-chat" class="tab-content hidden space-y-4">
            <div class="max-w-2xl mx-auto bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-4">
                <div>
                    <h2 class="text-sm font-bold text-white">Testar Assistente de Chat IA</h2>
                    <p class="text-xs text-slate-400">Simule uma mensagem de cliente para validar a resposta consultiva e defesa de escopo.</p>
                </div>

                <div class="space-y-2">
                    <textarea id="ai-chat-input" rows="3" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500" placeholder="Ex: Você faz um teste grátis antes de fecharmos?"></textarea>
                    
                    <div class="flex flex-wrap gap-1.5">
                        <button onclick="fillChatMessage('Você faz um teste grátis para eu ver seu código?')" class="text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-400 px-2 py-0.5 rounded">Teste Grátis</button>
                        <button onclick="fillChatMessage('Consegue dar um desconto no valor da proposta?')" class="text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-400 px-2 py-0.5 rounded">Desconto</button>
                        <button onclick="fillChatMessage('Como funciona sua garantia de entrega?')" class="text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-400 px-2 py-0.5 rounded">Garantia</button>
                    </div>
                </div>

                <button onclick="sendTestChatMessage()" id="btn-send-test-chat" class="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs py-2 rounded-lg transition shadow">
                    ✨ Gerar Resposta Consultiva com IA
                </button>

                <div id="ai-chat-response-box" class="hidden bg-slate-950 border border-purple-900/40 rounded-xl p-4 space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-[11px] font-semibold text-purple-300">Resposta Sugerida:</span>
                        <span id="ai-response-badge" class="bg-purple-500/20 text-purple-300 text-[10px] px-2 py-0.5 rounded font-mono">Gemini IA</span>
                    </div>
                    <div id="ai-chat-response-text" class="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap"></div>
                </div>
            </div>
        </section>
    </main>

    <!-- MODAL: VER / EDITAR PROPOSTA PENDENTE -->
    <div id="modal-proposal" class="hidden fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 w-full max-w-2xl rounded-2xl p-6 space-y-4 shadow-2xl">
            <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                    <h3 class="text-sm font-bold text-white" id="modal-prop-title">Revisar Proposta</h3>
                    <p class="text-xs text-slate-400" id="modal-prop-client">Cliente: Carregando...</p>
                </div>
                <button onclick="closeProposalModal()" class="text-slate-400 hover:text-white text-lg">✕</button>
            </div>

            <div class="grid grid-cols-2 gap-3 text-xs">
                <div>
                    <label class="block text-slate-400 mb-1">Valor Proposto (R$)</label>
                    <input type="number" id="modal-prop-price" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-slate-100 font-semibold focus:outline-none focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-slate-400 mb-1">Prazo de Entrega</label>
                    <input type="text" id="modal-prop-days" readonly class="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-400">
                </div>
            </div>

            <div>
                <label class="block text-xs text-slate-400 mb-1">Texto da Proposta (Gerado com IA):</label>
                <textarea id="modal-prop-text" rows="8" class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-xs text-slate-100 leading-relaxed font-sans focus:outline-none focus:border-indigo-500"></textarea>
            </div>

            <div class="flex items-center justify-between pt-2 border-t border-slate-800 text-xs">
                <button onclick="rejectCurrentProposal()" class="text-rose-400 hover:text-rose-300 px-3 py-1.5 rounded-lg border border-rose-500/20 hover:bg-rose-500/10 transition">
                    Descartar Proposta
                </button>
                <div class="flex space-x-2">
                    <button onclick="closeProposalModal()" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg transition">
                        Cancelar
                    </button>
                    <button onclick="confirmApproveProposal()" id="btn-modal-approve" class="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-4 py-1.5 rounded-lg transition shadow flex items-center space-x-1.5">
                        <span>✅ Aprovar & Enviar Agora</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL: SESSÃO / CONECTAR 99FREELAS -->
    <div id="modal-login" class="hidden fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-2xl p-6 space-y-4 shadow-2xl">
            <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                <div class="flex items-center space-x-2">
                    <span class="text-lg">🔑</span>
                    <h3 class="text-sm font-bold text-white">Conectar Conta 99Freelas</h3>
                </div>
                <button onclick="closeLoginModal()" class="text-slate-400 hover:text-white text-lg">✕</button>
            </div>

            <div class="space-y-4 text-xs">
                <div class="bg-indigo-500/10 border border-indigo-500/20 rounded-xl p-3 text-indigo-300">
                    Insira seus cookies ou inicie o login automatizado para autorizar o bot a despachar propostas.
                </div>

                <div class="space-y-2">
                    <label class="block text-slate-300 font-semibold">Login Automático:</label>
                    <button onclick="startBrowserLogin()" id="btn-start-login" class="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold py-2 rounded-lg transition border border-slate-700">
                        🌐 Abrir Navegador para Login
                    </button>
                    <div id="login-status-box" class="text-slate-500 font-mono-code text-[11px]">Status: Aguardando início...</div>
                </div>

                <div class="space-y-2 pt-2 border-t border-slate-800">
                    <label class="block text-slate-300 font-semibold">Colar Cookies de Sessão (JSON ou String):</label>
                    <textarea id="cookies-input" rows="3" placeholder='{"JSESSIONID": "...", ...}' class="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-xs font-mono-code text-slate-200 focus:outline-none focus:border-indigo-500"></textarea>
                    <button onclick="saveSessionCookies()" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2 rounded-lg transition">
                        Salvar Cookies
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- MODAL: IA GEMINI -->
    <div id="modal-ai" class="hidden fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-2xl p-6 space-y-4 shadow-2xl">
            <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                <div class="flex items-center space-x-2">
                    <span class="text-lg">✨</span>
                    <h3 class="text-sm font-bold text-white">Configuração da IA Google Gemini</h3>
                </div>
                <button onclick="closeAIModal()" class="text-slate-400 hover:text-white text-lg">✕</button>
            </div>

            <div class="space-y-3 text-xs">
                <div>
                    <label class="block text-slate-300 font-semibold mb-1">Chave de API (Google AI Studio):</label>
                    <input type="password" id="ai-key-input" placeholder="Cole sua API Key do Google Gemini..." class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500">
                </div>

                <div>
                    <label class="block text-slate-300 font-semibold mb-1">Modelo Selecionado:</label>
                    <select id="ai-model-select" class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500">
                        <option value="gemini-3.5-flash-lite">gemini-3.5-flash-lite (Recomendado / Ultra Rápido)</option>
                        <option value="gemini-2.5-flash">gemini-2.5-flash</option>
                        <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                        <option value="gemini-1.5-pro">gemini-1.5-pro</option>
                    </select>
                </div>

                <button onclick="saveAIConfig()" class="w-full bg-purple-600 hover:bg-purple-500 text-white font-semibold py-2 rounded-lg transition">
                    Salvar e Testar Conexão com Gemini
                </button>
            </div>
        </div>
    </div>

    <!-- Scripts JavaScript do Dashboard -->
    <script>
        let allProjects = [];
        let pendingProposals = [];
        let currentModalProposal = null;
        let lastLogCount = 0;

        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.getElementById(tabId).classList.remove('hidden');

            document.querySelectorAll('[id^="nav-tab-"]').forEach(btn => {
                btn.className = "px-4 py-2.5 border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition flex items-center space-x-1.5";
            });
            const activeBtn = document.getElementById('nav-' + tabId);
            if (activeBtn) {
                activeBtn.className = "px-4 py-2.5 border-b-2 border-indigo-500 text-white flex items-center space-x-1.5 transition";
            }
        }

        async function fetchData() {
            try {
                // KPIs
                const metrics = await fetch('/api/metrics').then(r => r.json());
                document.getElementById('kpi-connections-used').textContent = metrics.connections_used_today || 0;
                const pct = Math.min(100, ((metrics.connections_used_today || 0) / 3) * 100);
                document.getElementById('kpi-connections-bar').style.width = pct + '%';
                
                document.getElementById('kpi-projects-count').textContent = metrics.proposals_sent_count || 0;
                document.getElementById('kpi-conversion-rate').textContent = (metrics.conversion_rate_percent || 0) + '% aprovados';
                
                document.getElementById('kpi-revenue').textContent = 'R$ ' + (metrics.total_revenue_earned || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2});
                document.getElementById('kpi-pipeline').textContent = 'Pipeline: R$ ' + (metrics.pipeline_value || 0).toLocaleString('pt-BR', {minimumFractionDigits: 2});

                // Fila de Propostas Pendentes
                await fetchPendingProposals();

                // Feed de Projetos
                allProjects = await fetch('/api/projects').then(r => r.json());
                renderProjectsTable(allProjects);

                // Kanban
                const kanban = await fetch('/api/kanban').then(r => r.json());
                renderKanban(kanban);

                // Checa Sessão 99Freelas
                const sess = await fetch('/api/auth/status').then(r => r.json());
                updateSessionBadge(sess);
            } catch (err) {
                console.error("Erro na busca de dados:", err);
            }
        }

        async function fetchPendingProposals() {
            try {
                pendingProposals = await fetch('/api/proposals/pending').then(r => r.json());
                renderPendingProposals(pendingProposals);
            } catch (e) {
                console.error("Erro ao buscar propostas pendentes:", e);
            }
        }

        function renderPendingProposals(proposals) {
            const container = document.getElementById('pending-proposals-list');
            const kpiCount = document.getElementById('kpi-pending-count');
            const tabBadge = document.getElementById('tab-proposals-badge');
            const pulse = document.getElementById('kpi-pending-pulse');

            kpiCount.textContent = proposals.length;
            tabBadge.textContent = proposals.length;

            if (proposals.length > 0) {
                pulse.classList.remove('hidden');
            } else {
                pulse.classList.add('hidden');
            }

            if (proposals.length === 0) {
                container.innerHTML = `
                    <div class="bg-slate-900/60 border border-slate-800/80 rounded-xl p-8 text-center text-slate-500 text-xs">
                        <span class="text-2xl block mb-2">☕</span>
                        Tudo limpo! Nenhuma proposta pendente no momento. Quando o monitor identificar oportunidades com score alto, elas aparecerão aqui.
                    </div>
                `;
                return;
            }

            container.innerHTML = proposals.map(p => `
                <div class="bg-slate-900 border border-slate-800/90 hover:border-slate-700/80 p-4 rounded-xl shadow-sm transition space-y-3">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div class="space-y-1">
                            <div class="flex items-center space-x-2">
                                <span class="bg-purple-500/10 text-purple-300 font-bold px-2 py-0.5 rounded text-[11px] border border-purple-500/20">
                                    Score ${p.score ? p.score.toFixed(0) : '85'}/100
                                </span>
                                <h3 class="font-semibold text-sm text-slate-100">${escapeHtml(p.project_title || 'Projeto 99Freelas')}</h3>
                                ${p.project_url ? `<a href="${p.project_url}" target="_blank" class="text-xs text-indigo-400 hover:text-indigo-300">↗</a>` : ''}
                            </div>
                            <div class="text-[11px] text-slate-400 flex items-center space-x-3">
                                <span>Cliente: <strong>${escapeHtml(p.client_name || 'Cliente')}</strong></span>
                                <span>•</span>
                                <span>Concorrência: <strong>${p.proposals_count || 0} propostas</strong></span>
                                <span>•</span>
                                <span>Preço Sugerido: <strong class="text-emerald-400">R$ ${p.price.toFixed(2)}</strong> (${p.delivery_days} dias)</span>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2 self-end sm:self-auto">
                            <button onclick="openProposalModal(${p.id})" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 transition">
                                ✏️ Revisar / Editar
                            </button>
                            <button onclick="quickApproveProposal(${p.id})" class="text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-semibold px-3.5 py-1.5 rounded-lg transition shadow">
                                ✅ Aprovar & Enviar
                            </button>
                            <button onclick="quickRejectProposal(${p.id})" title="Descartar sem gastar conexão" class="text-xs bg-slate-800/60 hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 px-2.5 py-1.5 rounded-lg transition">
                                ✕
                            </button>
                        </div>
                    </div>

                    <div class="bg-slate-950/60 border border-slate-800/60 rounded-lg p-3 text-xs text-slate-300 line-clamp-2 leading-relaxed font-sans">
                        ${escapeHtml(p.proposal_text || '')}
                    </div>
                </div>
            `).join('');
        }

        async function quickApproveProposal(propId) {
            if (!confirm("Confirmar envio da proposta? Uma conexão será debitada da cota diária.")) return;
            try {
                const res = await fetch('/api/proposals/approve', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({proposal_id: propId})
                }).then(r => r.json());

                if (res.success) {
                    alert("🚀 " + res.message);
                    fetchData();
                } else {
                    alert("Erro: " + res.error);
                }
            } catch (e) {
                alert("Erro ao aprovar proposta: " + e.message);
            }
        }

        async function quickRejectProposal(propId) {
            if (!confirm("Descartar esta proposta? Nenhuma conexão será gasta.")) return;
            try {
                const res = await fetch('/api/proposals/reject', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({proposal_id: propId})
                }).then(r => r.json());

                if (res.success) {
                    fetchData();
                }
            } catch (e) {
                alert("Erro ao descartar: " + e.message);
            }
        }

        function openProposalModal(propId) {
            const p = pendingProposals.find(item => item.id === propId);
            if (!p) return;
            currentModalProposal = p;

            document.getElementById('modal-prop-title').textContent = p.project_title || 'Revisar Proposta';
            document.getElementById('modal-prop-client').textContent = `Cliente: ${p.client_name || 'Não informado'} • Concorrência: ${p.proposals_count || 0} propostas`;
            document.getElementById('modal-prop-price').value = p.price || 0;
            document.getElementById('modal-prop-days').value = `${p.delivery_days || 2} dias úteis`;
            document.getElementById('modal-prop-text').value = p.proposal_text || '';

            document.getElementById('modal-proposal').classList.remove('hidden');
        }

        function closeProposalModal() {
            document.getElementById('modal-proposal').classList.add('hidden');
            currentModalProposal = null;
        }

        async function confirmApproveProposal() {
            if (!currentModalProposal) return;
            const price = parseFloat(document.getElementById('modal-prop-price').value);
            const text = document.getElementById('modal-prop-text').value.trim();

            if (!text) {
                alert("O texto da proposta não pode ficar vazio!");
                return;
            }

            const btn = document.getElementById('btn-modal-approve');
            btn.disabled = true;
            btn.innerHTML = `<span>⏳ Despachando...</span>`;

            try {
                const res = await fetch('/api/proposals/approve', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        proposal_id: currentModalProposal.id,
                        price: price,
                        edited_text: text
                    })
                }).then(r => r.json());

                if (res.success) {
                    closeProposalModal();
                    alert("🎉 " + res.message);
                    fetchData();
                } else {
                    alert("Erro: " + res.error);
                }
            } catch (e) {
                alert("Erro ao aprovar proposta: " + e.message);
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<span>✅ Aprovar & Enviar Agora</span>`;
            }
        }

        async function rejectCurrentProposal() {
            if (!currentModalProposal) return;
            await quickRejectProposal(currentModalProposal.id);
            closeProposalModal();
        }

        function renderProjectsTable(projects) {
            const tbody = document.getElementById('projects-table');
            if (projects.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-6 text-center text-slate-500">Nenhum projeto registrado ainda.</td></tr>';
                return;
            }

            tbody.innerHTML = projects.slice(0, 20).map(p => {
                const isApproved = p.status === 'approved' || p.status === 'proposal_sent';
                const statusBadge = isApproved 
                    ? '<span class="bg-emerald-500/10 text-emerald-400 text-[10px] px-2 py-0.5 rounded-full border border-emerald-500/20 font-medium">Aprovado</span>'
                    : '<span class="bg-rose-500/10 text-rose-400 text-[10px] px-2 py-0.5 rounded-full border border-rose-500/20">Descartado</span>';

                return `
                    <tr class="hover:bg-slate-900/40 transition">
                        <td class="px-4 py-3">
                            <div class="font-medium text-slate-200 line-clamp-1">${escapeHtml(p.title)}</div>
                            <div class="text-[11px] text-slate-500">${escapeHtml(p.client_name || 'Cliente')}</div>
                        </td>
                        <td class="px-4 py-3 text-slate-400">${p.proposals_count} propostas</td>
                        <td class="px-4 py-3 font-semibold ${p.score >= 80 ? 'text-emerald-400' : 'text-slate-400'}">
                            ${p.score ? p.score.toFixed(0) : '0'}/100
                        </td>
                        <td class="px-4 py-3">${statusBadge}</td>
                        <td class="px-4 py-3 text-right">
                            <a href="${p.url}" target="_blank" class="text-indigo-400 hover:text-indigo-300 font-medium">Abrir ↗</a>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function filterProjectsTable(type) {
            document.querySelectorAll('.feed-filter-btn').forEach(b => {
                b.className = "feed-filter-btn px-2.5 py-1 rounded-md text-xs text-slate-400 hover:text-white";
            });
            event.target.className = "feed-filter-btn px-2.5 py-1 rounded-md text-xs bg-slate-800 text-white font-medium";

            if (type === 'all') {
                renderProjectsTable(allProjects);
            } else if (type === 'approved') {
                renderProjectsTable(allProjects.filter(p => p.status === 'approved' || p.status === 'proposal_sent'));
            } else {
                renderProjectsTable(allProjects.filter(p => p.status === 'rejected'));
            }
        }

        function renderKanban(columns) {
            renderColumn('col-todo', 'badge-todo', columns['a_fazer'] || [], 'todo');
            renderColumn('col-inprogress', 'badge-inprogress', columns['em_andamento'] || [], 'inprogress');
            renderColumn('col-review', 'badge-review', columns['revisao_homologacao'] || [], 'review');
            renderColumn('col-done', 'badge-done', columns['concluido'] || [], 'done');
        }

        function renderColumn(colId, badgeId, tasks, type) {
            const container = document.getElementById(colId);
            document.getElementById(badgeId).textContent = tasks.length;
            if (tasks.length === 0) {
                container.innerHTML = '<div class="text-[11px] text-slate-600 text-center py-4">Vazio</div>';
                return;
            }
            container.innerHTML = tasks.map(t => `
                <div class="bg-slate-800/60 border border-slate-700/50 p-2.5 rounded-lg text-xs space-y-1">
                    <div class="font-medium text-slate-200">${escapeHtml(t.title)}</div>
                    <div class="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                        <span>#${t.id.slice(0,6)}</span>
                        <div class="space-x-1">
                            ${type !== 'todo' ? `<button onclick="moveTask('${t.id}', '${prevStatus(type)}')" class="hover:text-white">◀</button>` : ''}
                            ${type !== 'done' ? `<button onclick="moveTask('${t.id}', '${nextStatus(type)}')" class="hover:text-white">▶</button>` : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function prevStatus(t) { return t === 'inprogress' ? 'a_fazer' : (t === 'review' ? 'em_andamento' : 'revisao_homologacao'); }
        function nextStatus(t) { return t === 'todo' ? 'em_andamento' : (t === 'inprogress' ? 'revisao_homologacao' : 'concluido'); }

        async function moveTask(id, st) {
            await fetch('/api/kanban/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_id: id, new_status: st})
            });
            fetchData();
        }

        async function promptNewTask() {
            const title = prompt("Título da Tarefa:");
            if (!title) return;
            await fetch('/api/kanban/task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title: title, description: "", project_id: "custom"})
            });
            fetchData();
        }

        // Monitor e Logs
        async function fetchMonitorState() {
            try {
                const st = await fetch('/api/monitor/status').then(r => r.json());
                const badge = document.getElementById('badge-monitor');
                const btn = document.getElementById('btn-toggle-monitor');
                const icon = document.getElementById('icon-monitor');
                const lbl = document.getElementById('label-monitor');

                if (st.running) {
                    badge.className = "px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                    badge.textContent = "🟢 Monitor Ativo";
                    btn.className = "text-xs font-semibold px-3 py-1.5 rounded-lg border transition shadow-sm bg-amber-600 hover:bg-amber-500 text-white border-amber-500/30 flex items-center space-x-1.5";
                    icon.textContent = "⏸";
                    lbl.textContent = "Pausar Monitor";
                } else {
                    badge.className = "px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-800 text-slate-400 border border-slate-700";
                    badge.textContent = "⏸️ Monitor Pausado";
                    btn.className = "text-xs font-semibold px-3 py-1.5 rounded-lg border transition shadow-sm bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-500/30 flex items-center space-x-1.5";
                    icon.textContent = "▶";
                    lbl.textContent = "Ligar Monitor";
                }

                // Logs
                const logsRes = await fetch('/api/monitor/logs').then(r => r.json());
                renderLogs(logsRes.logs || []);
            } catch (e) {
                console.error("Erro ao checar monitor:", e);
            }
        }

        function renderLogs(logs) {
            if (logs.length === lastLogCount) return;
            lastLogCount = logs.length;
            const consoleEl = document.getElementById('terminal-console');

            if (logs.length === 0) {
                consoleEl.innerHTML = '<div class="text-slate-500">// Aguardando registros do monitor...</div>';
                return;
            }

            consoleEl.innerHTML = logs.map(line => {
                let colorClass = "text-slate-300";
                if (line.includes("APROVADO") || line.includes("SUCESSO") || line.includes("AUTENTICAÇÃO")) {
                    colorClass = "text-emerald-400 font-semibold";
                } else if (line.includes("Descartado")) {
                    colorClass = "text-slate-500";
                } else if (line.includes("⚠️")) {
                    colorClass = "text-amber-400";
                } else if (line.includes("❌")) {
                    colorClass = "text-rose-400";
                } else if (line.includes("📡") || line.includes("🔎")) {
                    colorClass = "text-sky-300";
                }
                return `<div class="${colorClass}">${escapeHtml(line)}</div>`;
            }).join('');

            if (document.getElementById('chk-autoscroll').checked) {
                consoleEl.scrollTop = consoleEl.scrollHeight;
            }
        }

        async function toggleMonitor() {
            const st = await fetch('/api/monitor/status').then(r => r.json());
            const endpoint = st.running ? '/api/monitor/stop' : '/api/monitor/start';
            await fetch(endpoint, { method: 'POST' });
            fetchMonitorState();
        }

        async function clearTerminalLogs() {
            await fetch('/api/monitor/clear-logs', { method: 'POST' });
            lastLogCount = 0;
            document.getElementById('terminal-console').innerHTML = '<div class="text-slate-500">// Histórico limpo.</div>';
        }

        function updateSessionBadge(st) {
            const badge = document.getElementById('badge-session');
            const alert = document.getElementById('session-alert-banner');
            if (st.authenticated) {
                badge.className = "px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                badge.textContent = "🔑 99F Conectado";
                if (alert) alert.classList.add('hidden');
            } else {
                badge.className = "px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20 cursor-pointer";
                badge.textContent = "⚠️ 99F Desconectado";
                if (alert) alert.classList.remove('hidden');
            }
        }

        async function startBrowserLogin() {
            const statusBox = document.getElementById('login-status-box');
            if (statusBox) statusBox.textContent = "⏳ Abrindo navegador...";
            try {
                const res = await fetch('/api/auth/login', { method: 'POST' }).then(r => r.json());
                if (statusBox) statusBox.textContent = "🌐 " + (res.message || "Aguardando confirmação");
            } catch (e) {
                if (statusBox) statusBox.textContent = "❌ " + e.message;
            }
        }

        // Modais e IA
        function openLoginModal() { document.getElementById('modal-login').classList.remove('hidden'); }
        function closeLoginModal() { document.getElementById('modal-login').classList.add('hidden'); }
        function openAIModal() { document.getElementById('modal-ai').classList.remove('hidden'); }
        function closeAIModal() { document.getElementById('modal-ai').classList.add('hidden'); }

        async function saveSessionCookies() {
            const raw = document.getElementById('cookies-input').value.trim();
            if (!raw) return;
            const res = await fetch('/api/auth/cookies', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({cookies: raw})
            }).then(r => r.json());
            if (res.success) {
                alert("✅ Cookies salvos com sucesso!");
                closeLoginModal();
                fetchData();
            } else {
                alert("Erro: " + res.error);
            }
        }

        async function saveAIConfig() {
            const key = document.getElementById('ai-key-input').value.trim();
            const model = document.getElementById('ai-model-select').value;
            if (!key) return alert("Informe a chave da API Gemini!");
            const res = await fetch('/api/ai/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({api_key: key, model: model})
            }).then(r => r.json());
            if (res.success) {
                alert("🎉 " + res.message);
                closeAIModal();
            } else {
                alert("Erro: " + res.error);
            }
        }

        function fillChatMessage(t) { document.getElementById('ai-chat-input').value = t; }

        async function sendTestChatMessage() {
            const text = document.getElementById('ai-chat-input').value.trim();
            if (!text) return;
            const btn = document.getElementById('btn-send-test-chat');
            const box = document.getElementById('ai-chat-response-box');
            const resp = document.getElementById('ai-chat-response-text');
            btn.disabled = true;
            btn.textContent = "Pensando...";
            try {
                const res = await fetch('/api/ai/test-chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                }).then(r => r.json());
                box.classList.remove('hidden');
                resp.textContent = res.reply;
            } finally {
                btn.disabled = false;
                btn.textContent = "✨ Gerar Resposta Consultiva com IA";
            }
        }

        function escapeHtml(s) {
            return (s || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        // Init
        fetchData();
        fetchMonitorState();
        setInterval(fetchData, 10000);
        setInterval(fetchMonitorState, 3000);
    </script>
</body>
</html>
"""

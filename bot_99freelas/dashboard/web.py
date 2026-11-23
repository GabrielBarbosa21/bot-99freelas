"""Servidor Web do Painel de Controle Unificado com Monitor 24h, Terminal ao Vivo e Login Integrado (Fase 5+)."""

import os
import json
import logging
import webbrowser
import threading
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from bot_99freelas.dashboard.service import dashboard_service
from bot_99freelas.dashboard.kanban import kanban_manager
from bot_99freelas.dashboard.models import TaskStatus
from bot_99freelas.crawler.controller import monitor_controller
from bot_99freelas.crawler.browser_login import login_manager
from bot_99freelas.storage.db import db

logger = logging.getLogger("WebDashboard")

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel de Controle | Bot 99Freelas 24h</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .font-mono-code { font-family: 'JetBrains Mono', monospace; }
        /* Scrollbar customizada para terminal */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
    <!-- Header Principal -->
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <span class="text-2xl">🤖</span>
                <span class="font-bold text-lg text-white">Bot 99Freelas</span>
                
                <!-- Status do Monitor 24h -->
                <div id="monitor-badge-container">
                    <span id="monitor-badge" class="bg-slate-800 text-slate-400 text-xs px-2.5 py-0.5 rounded-full border border-slate-700 font-medium">
                        Verificando...
                    </span>
                </div>

                <!-- Status da Sessão de Cookies com gatilho de clique -->
                <button onclick="openLoginModal()" id="session-badge" class="cursor-pointer bg-slate-800 hover:bg-slate-700 text-slate-400 text-xs px-2.5 py-0.5 rounded-full border border-slate-700 font-medium transition">
                    🔑 Sessão
                </button>
            </div>

            <!-- Botões de Ação do Header -->
            <div class="flex items-center space-x-3">
                <button onclick="openLoginModal()" id="btn-auth-header" class="text-xs font-semibold px-3 py-1.5 rounded-lg border transition shadow-sm bg-indigo-600 hover:bg-indigo-500 text-white border-indigo-500/30">
                    🔑 Conectar Conta
                </button>
                <button id="btn-toggle-monitor" onclick="toggleMonitor()" class="text-xs font-semibold px-3.5 py-1.5 rounded-lg border transition shadow-sm bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-500/30">
                    ▶ Ligar Monitor
                </button>
                <button onclick="fetchData()" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition">
                    🔄 Atualizar
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <!-- Banner de Alerta de Sessão (Exibido se sessão expirada ou desconectada) -->
        <div id="session-alert-banner" class="hidden bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div class="flex items-center space-x-3">
                <span class="text-2xl">⚠️</span>
                <div>
                    <div class="font-bold text-amber-300 text-sm">Conta do 99Freelas Não Conectada ou Token Expirado</div>
                    <div class="text-xs text-slate-300 mt-0.5">Faça login com 1 clique para autorizar o bot a enviar propostas e monitorar oportunidades 24h sem interrupção.</div>
                </div>
            </div>
            <button onclick="openLoginModal()" class="whitespace-nowrap bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs px-4 py-2 rounded-lg transition shadow flex items-center space-x-1.5">
                <span>🔑 Conectar Conta Agora</span>
            </button>
        </div>

        <!-- KPIs / Métricas -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-sm">
                <div class="text-xs text-slate-400 font-medium">Faturamento Total</div>
                <div id="stat-revenue" class="text-2xl font-bold text-emerald-400 mt-1">R$ 0,00</div>
                <div class="text-xs text-slate-500 mt-2">Projetos aceitos/entregues</div>
            </div>

            <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-sm">
                <div class="text-xs text-slate-400 font-medium">Pipeline em Aberto</div>
                <div id="stat-pipeline" class="text-2xl font-bold text-sky-400 mt-1">R$ 0,00</div>
                <div class="text-xs text-slate-500 mt-2">Propostas em negociação</div>
            </div>

            <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-sm">
                <div class="text-xs text-slate-400 font-medium">Conexões Diárias</div>
                <div id="stat-connections" class="text-2xl font-bold text-amber-400 mt-1">0 / 3</div>
                <div class="text-xs text-slate-500 mt-2">Gastas hoje no 99Freelas</div>
            </div>

            <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl shadow-sm">
                <div class="text-xs text-slate-400 font-medium">Taxa de Conversão</div>
                <div id="stat-conversion" class="text-2xl font-bold text-violet-400 mt-1">0,0%</div>
                <div id="stat-props-count" class="text-xs text-slate-500 mt-2">0 propostas enviadas</div>
            </div>
        </div>

        <!-- Terminal de Operação ao Vivo (Card 5.1) -->
        <section class="space-y-3">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    <span class="text-base font-bold text-white">📟 Terminal de Operação ao Vivo</span>
                    <span id="terminal-pulse" class="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                    <span id="terminal-status-text" class="text-xs text-slate-400 font-mono">Varredura contínua ativa</span>
                </div>
                <div class="flex items-center space-x-2">
                    <button onclick="clearTerminalLogs()" class="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white px-2.5 py-1 rounded border border-slate-700 transition">
                        Limpar
                    </button>
                    <label class="flex items-center space-x-1.5 text-xs text-slate-400 cursor-pointer">
                        <input type="checkbox" id="chk-autoscroll" checked class="rounded bg-slate-800 border-slate-700 text-emerald-500 focus:ring-0">
                        <span>Auto-rolar</span>
                    </label>
                </div>
            </div>

            <div class="bg-black/90 border border-slate-800 rounded-xl p-4 shadow-inner">
                <div id="terminal-console" class="font-mono-code text-xs text-slate-300 h-64 overflow-y-auto space-y-1 select-text">
                    <div class="text-slate-500">// Terminal sincronizado com o monitor 24h em background...</div>
                </div>
            </div>
        </section>

        <!-- Quadro Kanban de Execução -->
        <section class="space-y-4">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-xl font-bold text-white">📋 Quadro de Execução (Kanban)</h2>
                    <p class="text-xs text-slate-400">Tarefas de entrega dos projetos aceitos para garantir 5 estrelas</p>
                </div>
                <button onclick="promptNewTask()" class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-2 rounded-lg shadow transition">
                    + Nova Tarefa
                </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <!-- Coluna: A Fazer -->
                <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col space-y-3">
                    <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                        <span class="text-sm font-semibold text-slate-300">📌 A Fazer</span>
                        <span id="badge-todo" class="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">0</span>
                    </div>
                    <div id="col-todo" class="space-y-2 flex-1 min-h-[150px]"></div>
                </div>

                <!-- Coluna: Em Andamento -->
                <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col space-y-3">
                    <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                        <span class="text-sm font-semibold text-amber-300">⚡ Em Andamento</span>
                        <span id="badge-inprogress" class="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">0</span>
                    </div>
                    <div id="col-inprogress" class="space-y-2 flex-1 min-h-[150px]"></div>
                </div>

                <!-- Coluna: Revisão / Homologação -->
                <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col space-y-3">
                    <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                        <span class="text-sm font-semibold text-sky-300">🔍 Revisão & Garantia</span>
                        <span id="badge-review" class="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">0</span>
                    </div>
                    <div id="col-review" class="space-y-2 flex-1 min-h-[150px]"></div>
                </div>

                <!-- Coluna: Concluído -->
                <div class="bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col space-y-3">
                    <div class="flex items-center justify-between pb-2 border-b border-slate-800">
                        <span class="text-sm font-semibold text-emerald-300">✅ Concluído</span>
                        <span id="badge-done" class="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">0</span>
                    </div>
                    <div id="col-done" class="space-y-2 flex-1 min-h-[150px]"></div>
                </div>
            </div>
        </section>

        <!-- Histórico Recente de Oportunidades do Feed -->
        <section class="space-y-4">
            <h2 class="text-xl font-bold text-white">📡 Oportunidades Monitoradas (Feed 99Freelas)</h2>
            <div class="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
                <table class="min-w-full divide-y divide-slate-800 text-left text-sm">
                    <thead class="bg-slate-800/40 text-slate-400 text-xs uppercase font-semibold">
                        <tr>
                            <th class="px-6 py-3">Projeto</th>
                            <th class="px-6 py-3">Concorrência</th>
                            <th class="px-6 py-3">Score Sniper</th>
                            <th class="px-6 py-3">Status</th>
                            <th class="px-6 py-3 text-right">Ação</th>
                        </tr>
                    </thead>
                    <tbody id="projects-table" class="divide-y divide-slate-800/60 text-slate-300">
                        <tr>
                            <td colspan="5" class="px-6 py-8 text-center text-slate-500">
                                Carregando dados...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>
    </main>

    <!-- Modal Interativo de Autenticação / Login via Navegador -->
    <div id="modal-login" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full space-y-5 shadow-2xl relative">
            <div class="flex items-center justify-between pb-3 border-b border-slate-800">
                <div class="flex items-center space-x-2.5">
                    <span class="text-xl">🌐</span>
                    <h3 class="font-bold text-white text-base">Conexão da Conta 99Freelas</h3>
                </div>
                <button onclick="closeLoginModal()" class="text-slate-400 hover:text-white text-sm transition">✕</button>
            </div>

            <div class="space-y-3.5 text-xs text-slate-300">
                <div class="bg-slate-800/60 p-4 rounded-xl border border-slate-700/50 space-y-2.5">
                    <div class="flex items-start space-x-2.5 text-emerald-400">
                        <span class="font-bold">1.</span>
                        <span>O navegador Google Chrome foi iniciado na tela oficial do 99Freelas.</span>
                    </div>
                    <div class="flex items-start space-x-2.5 text-sky-400">
                        <span class="font-bold">2.</span>
                        <span>Faça seu login com Google ou e-mail na janela aberta do Chrome.</span>
                    </div>
                    <div class="flex items-start space-x-2.5 text-violet-400">
                        <span class="font-bold">3.</span>
                        <span>Assim que logar, a sessão é capturada automaticamente para o bot!</span>
                    </div>
                </div>

                <!-- Live Status do Processo de Login -->
                <div class="flex items-center space-x-3 p-3.5 bg-black/60 rounded-xl border border-slate-800">
                    <div id="login-spinner" class="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
                    <div id="login-status-msg" class="font-mono text-xs text-slate-300">Iniciando navegador Chrome...</div>
                </div>
            </div>

            <div class="flex items-center justify-between pt-2 border-t border-slate-800/60">
                <button onclick="cancelLogin()" class="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs px-3.5 py-2 rounded-lg border border-slate-700 transition">
                    Cancelar
                </button>
                <div class="flex items-center space-x-2">
                    <button onclick="confirmLogin()" class="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs px-4 py-2 rounded-lg transition shadow flex items-center space-x-1.5">
                        <span>✅ Já Concluí o Login</span>
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let isMonitorRunning = false;
        let lastLogCount = 0;
        let loginPollTimer = null;

        async function fetchData() {
            try {
                const [resM, resK, resP] = await Promise.all([
                    fetch('/api/metrics').then(r => r.json()),
                    fetch('/api/kanban').then(r => r.json()),
                    fetch('/api/projects').then(r => r.json())
                ]);

                // 1. Atualiza Métricas
                document.getElementById('stat-revenue').textContent = `R$ ${resM.total_revenue_earned.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                document.getElementById('stat-pipeline').textContent = `R$ ${resM.pipeline_value.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
                document.getElementById('stat-connections').textContent = `${resM.connections_used_today} / 3`;
                document.getElementById('stat-conversion').textContent = `${resM.conversion_rate_percent}%`;
                document.getElementById('stat-props-count').textContent = `${resM.proposals_sent_count} propostas enviadas (${resM.accepted_projects_count} aceitas)`;

                // 2. Atualiza Kanban
                renderKanbanColumn('col-todo', 'badge-todo', resK.a_fazer, 'todo');
                renderKanbanColumn('col-inprogress', 'badge-inprogress', resK.em_andamento, 'inprogress');
                renderKanbanColumn('col-review', 'badge-review', resK.revisao_homologacao, 'review');
                renderKanbanColumn('col-done', 'badge-done', resK.concluido, 'done');

                // 3. Atualiza Tabela de Projetos
                renderProjectsTable(resP);
            } catch (e) {
                console.error("Erro ao carregar dados:", e);
            }
        }

        async function fetchMonitorState() {
            try {
                const [resStatus, resLogs] = await Promise.all([
                    fetch('/api/monitor/status').then(r => r.json()),
                    fetch('/api/monitor/logs').then(r => r.json())
                ]);

                isMonitorRunning = resStatus.running;
                const badge = document.getElementById('monitor-badge');
                const btnToggle = document.getElementById('btn-toggle-monitor');
                const pulse = document.getElementById('terminal-pulse');
                const statusText = document.getElementById('terminal-status-text');

                if (isMonitorRunning) {
                    badge.className = "bg-emerald-500/10 text-emerald-400 text-xs px-2.5 py-0.5 rounded-full border border-emerald-500/20 font-medium";
                    badge.innerHTML = "🟢 Monitor Ativo 24h";
                    btnToggle.className = "text-xs font-semibold px-3.5 py-1.5 rounded-lg border transition shadow-sm bg-rose-600 hover:bg-rose-500 text-white border-rose-500/30";
                    btnToggle.textContent = "⏸ Pausar Monitor";
                    pulse.classList.remove('hidden');
                    statusText.textContent = `Varredura contínua ativa (${resStatus.cycles_completed} ciclos | última: ${resStatus.last_scan})`;
                } else {
                    badge.className = "bg-rose-500/10 text-rose-400 text-xs px-2.5 py-0.5 rounded-full border border-rose-500/20 font-medium";
                    badge.innerHTML = "🔴 Monitor Pausado";
                    btnToggle.className = "text-xs font-semibold px-3.5 py-1.5 rounded-lg border transition shadow-sm bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-500/30";
                    btnToggle.textContent = "▶ Iniciar Monitor";
                    pulse.classList.add('hidden');
                    statusText.textContent = "Monitor em pausa";
                }

                // Sessão e Alerta de Login
                const sessionBadge = document.getElementById('session-badge');
                const sessionBanner = document.getElementById('session-alert-banner');
                const btnAuthHeader = document.getElementById('btn-auth-header');

                if (resStatus.session_valid) {
                    sessionBadge.className = "cursor-pointer bg-emerald-500/10 text-emerald-400 text-xs px-2.5 py-0.5 rounded-full border border-emerald-500/20 font-medium";
                    sessionBadge.innerHTML = "🔑 Sessão Ativa";
                    sessionBanner.classList.add('hidden');
                    btnAuthHeader.className = "text-xs font-semibold px-3 py-1.5 rounded-lg border transition shadow-sm bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700";
                    btnAuthHeader.textContent = "🔄 Renovar Conta";
                } else {
                    sessionBadge.className = "cursor-pointer bg-amber-500/10 text-amber-400 text-xs px-2.5 py-0.5 rounded-full border border-amber-500/20 font-medium animate-pulse";
                    sessionBadge.innerHTML = "⚠️ Sessão Expirada";
                    sessionBanner.classList.remove('hidden');
                    btnAuthHeader.className = "text-xs font-semibold px-3 py-1.5 rounded-lg border transition shadow-sm bg-amber-600 hover:bg-amber-500 text-white border-amber-500/30 animate-pulse";
                    btnAuthHeader.textContent = "🔑 Conectar Conta";
                }

                // Render logs
                renderTerminalLogs(resLogs.logs || []);
            } catch (e) {
                console.error("Erro ao consultar status do monitor:", e);
            }
        }

        async function toggleMonitor() {
            const endpoint = isMonitorRunning ? '/api/monitor/stop' : '/api/monitor/start';
            await fetch(endpoint, { method: 'POST' });
            fetchMonitorState();
        }

        // --- Gerenciamento do Modal e Fluxo de Login ---
        async function openLoginModal() {
            const modal = document.getElementById('modal-login');
            modal.classList.remove('hidden');
            document.getElementById('login-status-msg').textContent = "Iniciando Google Chrome...";
            document.getElementById('login-spinner').className = "w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin";

            // Dispara início do login
            await fetch('/api/auth/login', { method: 'POST' });

            // Inicia polling de status do login
            if (loginPollTimer) clearInterval(loginPollTimer);
            loginPollTimer = setInterval(pollLoginStatus, 1500);
        }

        async function pollLoginStatus() {
            try {
                const res = await fetch('/api/auth/status').then(r => r.json());
                const msgEl = document.getElementById('login-status-msg');
                const spinnerEl = document.getElementById('login-spinner');

                if (res.status_message) {
                    msgEl.textContent = res.status_message;
                }

                if (res.session_valid) {
                    spinnerEl.className = "hidden";
                    msgEl.className = "font-mono text-xs text-emerald-400 font-bold";
                    msgEl.textContent = "🎉 Sucesso! Conta conectada e cookies salvos!";
                    clearInterval(loginPollTimer);
                    setTimeout(() => {
                        closeLoginModal();
                        fetchMonitorState();
                        fetchData();
                    }, 2000);
                }
            } catch (e) {
                console.error("Erro ao consultar status de login:", e);
            }
        }

        async function confirmLogin() {
            const msgEl = document.getElementById('login-status-msg');
            msgEl.textContent = "Capturando cookies da janela do Chrome...";
            await fetch('/api/auth/confirm', { method: 'POST' });
        }

        async function cancelLogin() {
            await fetch('/api/auth/cancel', { method: 'POST' });
            closeLoginModal();
        }

        function closeLoginModal() {
            if (loginPollTimer) clearInterval(loginPollTimer);
            document.getElementById('modal-login').classList.add('hidden');
        }

        function renderTerminalLogs(logs) {
            const consoleEl = document.getElementById('terminal-console');
            if (logs.length === lastLogCount) return;
            lastLogCount = logs.length;

            if (logs.length === 0) {
                consoleEl.innerHTML = '<div class="text-slate-500">// Aguardando registros do monitor...</div>';
                return;
            }

            consoleEl.innerHTML = logs.map(line => {
                let colorClass = "text-slate-300";
                if (line.includes("APROVADO") || line.includes("SUCESSO") || line.includes("Prioridade") || line.includes("AUTENTICAÇÃO CONCLUÍDA")) {
                    colorClass = "text-emerald-400 font-semibold";
                } else if (line.includes("Descartado")) {
                    colorClass = "text-slate-500";
                } else if (line.includes("MODO AUTÔNOMO")) {
                    colorClass = "text-amber-300 font-semibold";
                } else if (line.includes("⚠️") || line.includes("Aviso")) {
                    colorClass = "text-amber-400";
                } else if (line.includes("❌") || line.includes("Erro")) {
                    colorClass = "text-rose-400 font-semibold";
                } else if (line.includes("📡") || line.includes("🔎")) {
                    colorClass = "text-sky-300";
                }
                return `<div class="${colorClass}">${escapeHtml(line)}</div>`;
            }).join('');

            const autoScroll = document.getElementById('chk-autoscroll').checked;
            if (autoScroll) {
                consoleEl.scrollTop = consoleEl.scrollHeight;
            }
        }

        async function clearTerminalLogs() {
            await fetch('/api/monitor/clear-logs', { method: 'POST' });
            lastLogCount = 0;
            document.getElementById('terminal-console').innerHTML = '<div class="text-slate-500">// Histórico de logs limpo.</div>';
        }

        function renderKanbanColumn(containerId, badgeId, tasks, colType) {
            const container = document.getElementById(containerId);
            const badge = document.getElementById(badgeId);
            badge.textContent = tasks.length;
            container.innerHTML = '';

            if (tasks.length === 0) {
                container.innerHTML = '<div class="text-xs text-slate-600 text-center py-6">Vazio</div>';
                return;
            }

            tasks.forEach(t => {
                const card = document.createElement('div');
                card.className = "bg-slate-800/80 border border-slate-700/60 p-3 rounded-lg shadow-sm hover:border-slate-600 transition space-y-2";
                card.innerHTML = `
                    <div class="text-xs font-semibold text-slate-200">${escapeHtml(t.title)}</div>
                    ${t.description ? `<div class="text-xs text-slate-400 line-clamp-2">${escapeHtml(t.description)}</div>` : ''}
                    <div class="flex items-center justify-between pt-2 border-t border-slate-700/40 text-[10px]">
                        <span class="text-slate-500 font-mono">${t.id}</span>
                        <div class="flex space-x-1">
                            ${colType !== 'todo' ? `<button onclick="moveTask('${t.id}', '${prevStatus(colType)}')" class="hover:text-white text-slate-400">◀</button>` : ''}
                            ${colType !== 'done' ? `<button onclick="moveTask('${t.id}', '${nextStatus(colType)}')" class="hover:text-white text-slate-400">▶</button>` : ''}
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function prevStatus(type) {
            if (type === 'inprogress') return 'a_fazer';
            if (type === 'review') return 'em_andamento';
            if (type === 'done') return 'revisao_homologacao';
            return 'a_fazer';
        }

        function nextStatus(type) {
            if (type === 'todo') return 'em_andamento';
            if (type === 'inprogress') return 'revisao_homologacao';
            if (type === 'review') return 'concluido';
            return 'concluido';
        }

        async function moveTask(taskId, newStatus) {
            await fetch('/api/kanban/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_id: taskId, new_status: newStatus})
            });
            fetchData();
        }

        async function promptNewTask() {
            const title = prompt("Título da Tarefa:");
            if (!title) return;
            const desc = prompt("Descrição / Observações (opcional):") || "";
            await fetch('/api/kanban/task', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title: title, description: desc, project_id: "custom"})
            });
            fetchData();
        }

        function renderProjectsTable(projects) {
            const tbody = document.getElementById('projects-table');
            tbody.innerHTML = '';
            if (projects.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-6 text-center text-slate-500">Nenhum projeto registrado ainda. O monitor alimentará esta lista.</td></tr>';
                return;
            }

            projects.slice(0, 15).forEach(p => {
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/30 transition";
                const isApproved = p.status === 'approved';
                const statusBadge = isApproved 
                    ? '<span class="bg-emerald-500/10 text-emerald-400 text-xs px-2.5 py-0.5 rounded-full border border-emerald-500/20 font-medium">Aprovado</span>'
                    : '<span class="bg-rose-500/10 text-rose-400 text-xs px-2.5 py-0.5 rounded-full border border-rose-500/20">Descartado</span>';

                tr.innerHTML = `
                    <td class="px-6 py-4 font-medium text-slate-200">
                        <div class="line-clamp-1">${escapeHtml(p.title)}</div>
                        <div class="text-xs text-slate-500 mt-0.5">${escapeHtml(p.client_name || 'Cliente')}</div>
                    </td>
                    <td class="px-6 py-4 text-slate-400 text-xs">${p.proposals_count} propostas</td>
                    <td class="px-6 py-4 text-xs font-semibold ${p.score >= 90 ? 'text-emerald-300 font-bold' : (p.score >= 70 ? 'text-emerald-400' : 'text-slate-400')}">
                        ${p.score.toFixed(1)}/100
                    </td>
                    <td class="px-6 py-4">${statusBadge}</td>
                    <td class="px-6 py-4 text-right">
                        <a href="${p.url}" target="_blank" class="text-xs text-blue-400 hover:text-blue-300 font-medium">Abrir ↗</a>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

        function escapeHtml(str) {
            if (!str) return "";
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        // Inicialização
        fetchData();
        fetchMonitorState();
        setInterval(fetchData, 10000);
        setInterval(fetchMonitorState, 3000);
    </script>
</body>
</html>
"""


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Manipulador de requisições do Dashboard Web Unificado."""

    def log_message(self, format, *args):
        # Desativa logs HTTP de acesso no terminal
        pass

    def _send_json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            payload = HTML_TEMPLATE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        elif path == "/api/metrics":
            metrics = dashboard_service.calculate_metrics()
            self._send_json(metrics.model_dump())

        elif path == "/api/kanban":
            columns = kanban_manager.get_board_columns()
            serializable = {
                k: [t.model_dump() for t in v] for k, v in columns.items()
            }
            self._send_json(serializable)

        elif path == "/api/projects":
            projs_dict = db._data.get("projects", {})
            projs_list = list(projs_dict.values())
            projs_list.reverse()
            self._send_json(projs_list)

        elif path == "/api/monitor/status":
            self._send_json(monitor_controller.get_status())

        elif path == "/api/monitor/logs":
            self._send_json({"logs": monitor_controller.get_logs()})

        elif path == "/api/auth/status":
            self._send_json(login_manager.get_status())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if parsed.path == "/api/monitor/start":
            res = monitor_controller.start()
            self._send_json(res)

        elif parsed.path == "/api/monitor/stop":
            res = monitor_controller.stop()
            self._send_json(res)

        elif parsed.path == "/api/monitor/clear-logs":
            monitor_controller.clear_logs()
            self._send_json({"success": True})

        elif parsed.path == "/api/auth/login":
            res = login_manager.start_login()
            self._send_json(res)

        elif parsed.path == "/api/auth/confirm":
            res = login_manager.confirm_login()
            self._send_json(res)

        elif parsed.path == "/api/auth/cancel":
            res = login_manager.cancel_login()
            self._send_json(res)

        elif parsed.path == "/api/kanban/move":
            task_id = data.get("task_id")
            new_status = data.get("new_status")
            if task_id and new_status:
                try:
                    status_enum = TaskStatus(new_status)
                    success = kanban_manager.move_task(task_id, status_enum)
                    self._send_json({"success": success})
                    return
                except ValueError:
                    pass
            self._send_json({"success": False, "error": "Invalid params"}, 400)

        elif parsed.path == "/api/kanban/task":
            title = data.get("title", "Nova Tarefa")
            desc = data.get("description", "")
            proj_id = data.get("project_id", "custom")
            task = kanban_manager.create_task(proj_id, title, desc)
            self._send_json({"success": True, "task": task.model_dump()})

        else:
            self.send_response(404)
            self.end_headers()


def start_web_dashboard(
    port: Optional[int] = None,
    host: Optional[str] = None,
    open_browser: Optional[bool] = None,
    auto_start_monitor: bool = True,
) -> None:
    """Inicia o servidor web (local ou em nuvem/Docker) e ativa o monitor 24h em background."""
    target_host = host or os.getenv("HOST", "0.0.0.0")
    target_port = port or int(os.getenv("PORT", "5000"))

    # Em contêineres Docker ou ambientes de nuvem, não tenta abrir navegador gráfico
    is_cloud = bool(
        os.getenv("DOCKER")
        or os.getenv("RAILWAY_ENVIRONMENT")
        or os.getenv("RENDER")
        or os.getenv("FLY_APP_NAME")
    )
    should_open_browser = open_browser if open_browser is not None else (not is_cloud)

    server = HTTPServer((target_host, target_port), DashboardRequestHandler)
    url = f"http://{'localhost' if target_host in ('0.0.0.0', '127.0.0.1') else target_host}:{target_port}"

    print("\n" + "=" * 65)
    print(f" 🌐 PAINEL DE CONTROLE WEB UNIFICADO 24H: {url} (Host: {target_host})")
    print("=" * 65)
    print("👉 Acompanhe métricas, quadro Kanban, terminal ao vivo e feed do 99Freelas!")
    print("👉 Faça login na sua conta do 99Freelas diretamente pelo botão no painel.")
    print("👉 Pressione Ctrl+C para encerrar o painel.\n")

    # Inicia automaticamente o monitor em segundo plano (Card 5.1)
    if auto_start_monitor:
        monitor_controller.start()

    if should_open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Encerrando painel web e monitor...")
        monitor_controller.stop()
        server.server_close()


if __name__ == "__main__":
    start_web_dashboard()

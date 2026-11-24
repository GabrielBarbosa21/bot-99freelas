# 🗺️ Roadmap de Desenvolvimento - Bot 99Freelas

Este roadmap define as 4 fases de implementação do projeto. Cada item corresponde a um card no Kanban do projeto.

---

### 📌 Fase 1: Motor de Filtragem, Precificação e Propostas
- [x] **Card 1.1**: Configurar repositório, branches (`main`, `develop`) e skills no `.agents/skills`.
- [x] **Card 1.2**: Implementar modelo de dados de projetos e filtro de relevância (descarte de spam e clientes com histórico ruim).
- [x] **Card 1.3**: Criar algoritmo de precificação de entrada (cálculo de complexidade com desconto de penetração de mercado).
- [x] **Card 1.4**: Desenvolver o gerador de propostas humanizadas (prompt de copywriting baseado no `sales-automator`).
- [x] **Card 1.5**: Testes de simulação em projetos reais do 99Freelas sem envio (modo teste).

---

### 📌 Fase 2: Automação e Monitoramento no 99Freelas
- [x] **Card 2.1**: Script de login e persistência de sessão (armazenamento seguro de cookies).
- [x] **Card 2.2**: Crawler assíncrono para varredura do feed de novos projetos em tempo real.
- [x] **Card 2.3**: Sistema de notificação semiautomática (envio de alerta com proposta pronta para aprovação com 1 clique).
- [x] **Card 2.4**: Módulo de envio de propostas autenticado.

---

### 📌 Fase 3: Módulo de Conversação Inteligente
- [x] **Card 3.1**: Monitoramento da caixa de mensagens / chat do 99Freelas.
- [x] **Card 3.2**: Classificador de intenção do cliente (dúvida técnica, negociação de preço, prazo, fechamento).
- [x] **Card 3.3**: Gerador de respostas em tempo real com proteção de escopo (`no-free-work`).

---

### 📌 Fase 4: Painel de Controle (Dashboard) & Tarefas
- [x] **Card 4.1**: Backend de gestão de propostas e conexões gastas/restantes.
- [x] **Card 4.2**: Quadro Kanban interativo para tarefas dos projetos aceitos.
- [x] **Card 4.3**: Métricas de conversão e faturamento acumulado.

---

### 📌 Fase 5: Operação Contínua 24h & Modo Sniper
- [x] **Card 5.1**: Unificação do Monitor 24h diretamente no Painel Web (`http://localhost:5000`) com terminal de logs ao vivo e controle de pausa/ativação.
- [x] **Card 5.2**: Filtro Sniper calibrado para oportunidades de desenvolvimento (Python, Automação, APIs, Scraping, IA, Bots) e descarte silencioso de categorias fora de escopo.
- [x] **Card 5.3**: Motor de resiliência e auto-recuperação contínua 24h (retentativas com backoff exponencial, checagem contínua de sessão e rotação automática de logs).
- [x] **Card 5.4**: Inicialização automática no Windows (`shell:startup`) e modo silencioso em segundo plano (`iniciar_silencioso.vbs`, `parar_bot.bat`).

---

### 📌 Fase 6: WhatsApp Copilot, Controle Granular & Segurança/Redesign do Painel
- [x] **Card 6.1**: Autenticação e Segurança do Painel Web (Login Seguro & Proteção de Rotas).
- [ ] **Card 6.2**: Redesign Visual Minimalista da UI (Dashboard Clean & Fila de Aprovação).
- [ ] **Card 6.3**: Controle Granular de Varredura e Filtros de Busca (Tags, Categorias e Blacklist).
- [ ] **Card 6.4**: WhatsApp Copilot — Aprovação de Conexões e Propostas com 1 Comando.
- [ ] **Card 6.5**: Ponte Bidirecional WhatsApp ➔ Chat do 99Freelas (Notificação e Resposta).
- [ ] **Card 6.6**: Relatório Periódico de 1 Hora no WhatsApp (Métricas e Execução).



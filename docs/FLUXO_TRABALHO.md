# 🔄 Fluxo de Trabalho Completo — Bot 99Freelas

Este documento descreve detalhadamente o fluxo de operação, as regras de negócio, a integração com Inteligência Artificial e as salvaguardas de segurança do **bot-99freelas**. Serve como especificação técnica e contexto central para as próximas etapas de desenvolvimento.

---

## 1. Visão Geral da Arquitetura

O bot atua como um operador autônomo e consultivo no marketplace 99Freelas, com 4 objetivos principais:
1. **Identificar projetos de alto valor e alta compatibilidade técnica** (Python, Automação, Web Scraping, APIs).
2. **Economizar conexões** descartando concorrência saturada e armadilhas de escopo.
3. **Gerar propostas consultivas com autoridade**, incorporando insights técnicos em tempo real gerados por IA.
4. **Atender clientes no chat com postura consultiva e defesa de escopo (*No-Free-Work*)**, convertendo contatos em contratos fechados dentro da plataforma.

---

## 2. Diagrama do Fluxo de Trabalho (End-to-End)

```mermaid
flowchart TD
    A["1. Varredura do Mercado (Crawler)"] -->|Busca a cada 60s novos projetos| B["2. Filtros Rápidos (Heurística)"]
    
    B -->|Muitas propostas (>15) ou orçamento < R$ 100| X1["❌ Descarte Rápido (Economiza Conexão)"]
    B -->|Projeto Aprovado| C["3. Triagem Profunda com IA (Google Gemini)"]
    
    C -->|Escopo abusivo / Inviável (Score < 50)| X2["❌ Descarte Justificado (Registrado nos Logs)"]
    C -->|Projeto de Alto Valor (Score >= 50)| D["4. Geração de Proposta Consultiva"]
    
    D -->|Incorpora 'Ângulo Técnico' gerado pela IA| E["5. Envio Seguro da Proposta"]
    E -->|Respeita Limite Diário (Máx 3 conexões/dia)| F["6. Monitoramento Contínuo do Chat"]
    
    F -->|Mensagem Recebida do Cliente| G["7. Classificação de Intenção & Resposta IA"]
    G -->|Tira dúvidas + Recusa testes grátis + CTA Fechamento| H["💬 Envio da Mensagem no 99Freelas"]
```

---

## 3. As 7 Etapas Detalhadas

### Etapa 1: Varredura de Mercado (Crawler)
- **Frequência:** A cada 60 segundos (ou conforme definido em `CHECK_INTERVAL_SECONDS`).
- **Escopo:** Varre páginas de projetos de TI, Desenvolvimento Web, Automação e Software.
- **Deduplicação:** Armazena os IDs dos projetos já visualizados no banco local (`bot_data.json` / SQLite) para nunca reprocessar o mesmo projeto.

### Etapa 2: Filtros Rápidos (Anti-Desperdício de Conexões)
- **Concorrência:** Se o projeto já tem mais de 15 a 20 propostas, é descartado imediatamente (alta dispersão de atenção do cliente e desperdício de conexão para perfis em crescimento).
- **Orçamento Mínimo:** Rejeita valores abaixo do piso (padrão: R$ 100).
- **Filtro Negativo:** Descarta trabalhos acadêmicos (TCC, monografias), digitação manual e termos suspeitos de golpes.

### Etapa 3: Avaliação Inteligente com Google Gemini
- O modelo ativo é o **`gemini-3.5-flash-lite`** (latência de ~1 segundo).
- Analisa o texto do projeto e extrai um objeto JSON estruturado:
  - `accepted`: (bool) Viabilidade técnica real.
  - `score`: (float 0 a 100) Pontuação de atratividade.
  - `reason`: Justificativa objetiva da decisão.
  - `technical_angle`: Abordagem técnica recomendada (ex: *"Propor script modular com Playwright e Pandas para contornar Cloudflare"*).
- **Proteção contra Armadilhas de Escopo:** Projetos que exigem soluções gigantescas por valores irrisórios (ex: "clone completo do Uber por R$ 150") são rejeitados com score próximo de zero.

### Etapa 4: Geração de Proposta Consultiva
- As propostas não são genéricas. A estrutura combina:
  1. Saudação personalizada com o nome do cliente.
  2. Validação imediata da dor do projeto.
  3. O **ângulo técnico formulado pela IA**, demonstrando autoridade prévia sem entregar código gratuito.
  4. Escopo claro com prazo realista e valor calculado pela estratégia de precificação.
  5. Chamada para Ação (CTA) direcionando para conversa no chat do 99Freelas.

### Etapa 5: Envio Seguro e Limites Anti-Ban
- **Limite Diário Rigoroso:** Configurado em `MAX_CONNECTIONS_PER_DAY=3` por padrão.
- **Intervalos com Jitter:** Variações aleatórias de tempo entre ações para manter o comportamento com aparência humana.
- **Modo Dry-Run (Simulação):** Quando ativado, simula o envio e registra o payload completo sem debitar conexões reais.

### Etapa 6: Monitoramento Ativo do Chat
- O serviço checa periodicamente se houve retorno de clientes em propostas enviadas.
- Mantém o histórico da conversa para manter coerência contextual.

### Etapa 7: Atendimento Consultivo da IA (Chat)
- As mensagens do cliente passam pelo Gemini com um prompt focado em vendas consultivas e **No-Free-Work**:
  - **Dúvidas Técnicas:** Responde com segurança e clareza didática.
  - **Pedidos de Teste Grátis:** Recusa educadamente, argumentando que a dedicação é integral, referenciando avaliações e sugerindo entrega modular ou garantias pós-entrega.
  - **Pedidos de Desconto:** Mantém a firmeza de valor ou sugere reduzir o escopo para caber no orçamento.
  - **Fechamento:** Sempre orienta o cliente a aceitar a proposta na plataforma para início imediato do desenvolvimento.

---

## 4. Salvaguardas e Tratamento de Erros

| Componente | Possível Falha | Como o Sistema Protege |
| :--- | :--- | :--- |
| **API do Gemini** | Timeout, cota excedida ou indisponibilidade | O sistema faz fallback gracioso para templates determinísticos testados. A aplicação **nunca trava** e nunca envia mensagens vazias. |
| **Sessão 99Freelas** | Cookies expirados ou revogados | O bot detecta perda de autenticação, interrompe tentativas de envio de propostas e registra alerta explícito no painel para reautenticação. |
| **Erros de Conexão** | Oscilação de rede no servidor | Tentativas com *exponential backoff* sem interromper o loop principal do daemon. |
| **Push para Git** | Bloqueio de secrets pelo GitHub | Chaves e sessões **nunca** devem ser commitadas nos arquivos de código; utilizam-se variáveis de ambiente (`.env` local ou `env-vars` no Render). |

---

## 5. Variáveis de Ambiente Críticas

| Variável | Descrição | Exemplo |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Chave de API do Google Gemini Studio | `AQ.Ab8RN6KYa...` |
| `GEMINI_MODEL` | Modelo Google Gemini em uso | `gemini-3.5-flash-lite` |
| `SESSION_COOKIES_JSON` | JSON com os cookies de sessão autenticada do 99Freelas | `{"JSESSIONID": "...", ...}` |
| `MAX_CONNECTIONS_PER_DAY`| Teto diário de propostas enviadas | `3` |
| `PORT` / `HOST` | Configurações do servidor web/dashboard | `5000` / `0.0.0.0` |

---

## 6. Procedimento Operacional: Pausa e Retomada

### Para Pausar o Serviço no Render (Modo Suspenso):
```bash
# Via API Render (ou pelo Dashboard do Render)
POST https://api.render.com/v1/services/srv-dc29snp7lnhs73a4sv60/suspend
```

### Para Reativar o Serviço no Render:
```bash
# Via API Render
POST https://api.render.com/v1/services/srv-dc29snp7lnhs73a4sv60/resume
```

---

## 7. Roteiro para Próximos Desenvolvimentos

1. **Dashboard UI Refinada:**
   - Adicionar botão visual direto de "Pausar/Retomar Monitor" no header do painel web.
   - Aba específica para visualização dos diálogos de chat e intervenção humana manual (caso você queira assumir o chat diretamente).
2. **Integração com Notificações:**
   - Configurar o bot do Telegram para apitar no celular quando a IA detectar um projeto nota 90+ ou quando um cliente responder no chat.
3. **Métricas de Conversão:**
   - Acompanhar taxa de resposta de propostas (quantas propostas enviadas viraram resposta no chat e quantas viraram contratação).

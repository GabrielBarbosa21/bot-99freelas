# ☁️ Guia de Deploy na Nuvem (Execução Contínua 24/7)

Este guia ensina como colocar o **Bot 99Freelas** rodando 24 horas por dia, 7 dias por semana na nuvem, sem depender do seu computador pessoal estar ligado.

---

## 🏆 Comparativo Rápido das Melhores Opções

| Provedor | Custo | Nível de Facilidade | Como Funciona |
|---|---|---|---|
| **Oracle Cloud (Always Free)** | **100% Grátis para Sempre** | Médio (VPS Linux) | Cria uma máquina virtual gratuita e roda com Docker. |
| **Railway / Render** | Grátis / Baixo custo (~$5) | **Muito Fácil (1 Clique)** | Conecta direto no seu GitHub e sobe automático. |
| **VPS Barata (Hetzner / Lightsail / DigitalOcean)** | ~$3.50 a $4/mês (~R$ 20) | Médio (VPS Linux) | Servidor próprio dedicado de altíssima estabilidade. |

---

## 🚀 Opção 1: Railway (A Mais Fácil e Rápida - 2 Minutos)

O Railway conecta direto com o seu repositório no GitHub e faz deploy automático usando o `Dockerfile` que já preparamos.

1. Acesse **[railway.app](https://railway.app)** e crie uma conta usando seu **GitHub**.
2. Clique em **"New Project"** ➔ **"Deploy from GitHub repo"**.
3. Selecione o repositório `GabrielBarbosa21/bot-99freelas`.
4. Vá na aba **"Variables"** do serviço no Railway e adicione:
   - `SESSION_COOKIES_JSON`: Abra o arquivo local `session_cookies.json`, copie todo o conteúdo e cole aqui.
   - `TELEGRAM_ALERT_ENABLED`: `true` (se você quiser receber alertas no Telegram)
   - `TELEGRAM_BOT_TOKEN`: Token do seu bot no Telegram (se configurado)
   - `TELEGRAM_CHAT_ID`: Seu ID do Telegram
5. Na aba **"Settings"**, clique em **"Generate Domain"** sob a seção *Networking*.
6. **Pronto!** O seu Painel Web e o Monitor 24h já estarão ativos no endereço gerado pelo Railway (com HTTPS automático).

---

## 🛡️ Opção 2: Oracle Cloud Always Free (100% Gratuita Para Sempre)

A Oracle oferece instâncias de computação gratuitas para sempre (*Always Free Tier*), com até 4 vCPUs e 24GB de RAM (Ampere ARM) ou 1GB RAM (AMD x86).

### Passo a Passo:
1. Crie uma conta no **[Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)**.
2. No painel da Oracle, clique em **"Create a VM instance"**:
   - Imagem: **Ubuntu 22.04 ou 24.04 LTS**.
   - Baixe sua chave SSH privada (`.key`).
3. Conecte na sua máquina pelo terminal do Windows:
   ```bash
   ssh -i sua_chave.key ubuntu@ip_publico_da_sua_vm
   ```
4. Instale o Docker e Docker Compose na VM:
   ```bash
   sudo apt update && sudo apt install -y docker.io docker-compose git
   sudo usermod -aG docker $USER
   ```
5. Clone o repositório e configure:
   ```bash
   git clone https://github.com/GabrielBarbosa21/bot-99freelas.git
   cd bot-99freelas
   ```
6. Crie o arquivo `session_cookies.json` com seus cookies de autenticação:
   ```bash
   nano session_cookies.json
   # Cole o conteúdo do seu session_cookies.json local e salve (Ctrl+O, Enter, Ctrl+X)
   ```
7. Inicie o contêiner em segundo plano:
   ```bash
   docker-compose up -d
   ```
8. **Pronto!** O bot está rodando ininterruptamente 24/7.
   - Para ver os logs em tempo real: `docker logs -f bot_99freelas_24h`
   - O painel estará disponível na porta `5000` do IP da sua VM.

---

## 💡 Opção 3: VPS Barata (Hetzner, AWS Lightsail ou DigitalOcean)

Se preferir não passar pelo cadastro da Oracle Cloud, você pode alugar uma VPS Linux por ~R$ 20/mês na **Hetzner Cloud** (plano CX22) ou **AWS Lightsail** ($3.50/mês).

O processo é idêntico ao da Opção 2:
1. Acessar a VPS via SSH.
2. Executar `git clone https://github.com/GabrielBarbosa21/bot-99freelas.git`.
3. Inserir os cookies em `session_cookies.json`.
4. Executar `docker-compose up -d`.

---

## 🔑 Como manter a autenticação ativa na Nuvem?

1. **Geração dos Cookies no PC:**
   - Faça login na sua conta executando `painel.bat` ou `iniciar_login.bat` no seu computador uma vez.
   - Isso salvará o arquivo `session_cookies.json` autenticado.
2. **Envio para a Nuvem:**
   - No **Railway/Render**: Cole o conteúdo na variável de ambiente `SESSION_COOKIES_JSON`.
   - Na **VPS / Docker**: Copie o arquivo `session_cookies.json` para a pasta do bot.
3. Os cookies do 99Freelas permanecem válidos por longos períodos enquanto o bot mantiver a atividade diária.

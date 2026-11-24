# Imagem base leve com Python 3.12
FROM python:3.12-slim

# Evita criação de arquivos .pyc e força flush nos logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DOCKER=1 \
    PORT=5000 \
    HOST=0.0.0.0

WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY . .

# Cria diretórios para persistência de dados e logs
RUN mkdir -p /app/data /app/logs

# Expõe a porta do Painel Web
EXPOSE 5000

# Healthcheck para garantir que o painel e o bot estão ativos
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# Comando de inicialização: Inicia o painel web que aciona o monitor 24h
CMD ["python", "-m", "bot_99freelas", "dashboard"]

FROM python:3.12-slim

WORKDIR /app

# Instala dependencias de sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia arquivos do projeto
COPY pyproject.toml .
COPY src/ ./src/
COPY data_olist/ ./data_olist/

# Instala dependencias Python
RUN pip install --no-cache-dir -e "."

# Porta que o Streamlit usa
EXPOSE 10000

# Comando de start
CMD ["streamlit", "run", "src/app/main.py", "--server.port=10000", "--server.address=0.0.0.0", "--server.headless=true"]

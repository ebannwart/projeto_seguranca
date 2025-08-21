# Usa imagem oficial do Python
FROM python:3.11-slim

# Define diretório de trabalho
WORKDIR /app

# Copia os arquivos
COPY . /app

# Instala dependências
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Permite que o Railway defina a porta
ENV PORT=8000

# Expõe a porta
EXPOSE $PORT

# Comando para iniciar o app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
FROM python:3.11.9-alpine3.18
LABEL mantainer="byematheus@gmail.com"

# Essa variável de ambiente é usada para controlar se o Python deve 
# gravar arquivos de bytecode (.pyc) no disco. 1 = Não, 0 = Sim
ENV PYTHONDONTWRITEBYTECODE 1

# Define que a saída do Python será exibida imediatamente no console ou em 
# outros dispositivos de saída, sem ser armazenada em buffer.
# Em resumo, você verá os outputs do Python em tempo real.
ENV PYTHONUNBUFFERED 1

# altera o horario para sao paulo
ENV TZ="America/Sao_Paulo"

# Copia a pasta "wibdns" e "scripts" para dentro do container.
COPY wibdns /wibdns

# Entra na pasta wibdns no container
WORKDIR /wibdns

# RUN executa comandos em um shell dentro do container para construir a imagem. 
# O resultado da execução do comando é armazenado no sistema de arquivos da 
# imagem como uma nova camada.
# Agrupar os comandos em um único RUN pode reduzir a quantidade de camadas da 
# imagem e torná-la mais eficiente.
RUN apk add --no-cache git openssl3 build-base p7zip && \
  python -m venv /venv && \
  /venv/bin/pip install --upgrade pip && \
  /venv/bin/pip install -r /wibdns/requirements.txt && \
  adduser --disabled-password --no-create-home user001 && \
  chown -R user001:user001 /venv && \
  chown -R user001:user001 /wibdns

# Muda o usuário para user001
USER user001

# comando para rodar docker
# docker-compose up -d
# docker compose up -d --build
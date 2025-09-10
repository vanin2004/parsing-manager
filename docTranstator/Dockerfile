FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    libreoffice \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    curl \
    ca-certificates \
    fonts-dejavu \
    locales \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
RUN ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app
COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

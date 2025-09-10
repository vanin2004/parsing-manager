FROM python:3.11

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    locales\
    && rm -rf /var/lib/apt/lists/*

RUN sed -i '/ru_RU.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
RUN ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
ENV LANG ru_RU.UTF-8
ENV LANGUAGE ru_RU:ru
ENV LC_ALL ru_RU.UTF-8

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
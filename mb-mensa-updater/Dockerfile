FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache git openssh-client

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY update.sh .
RUN chmod +x update.sh

ENV TZ=Europe/Zurich

# Monday 6am CEST
RUN echo "0 6 * * 1 /app/update.sh >> /var/log/cron.log 2>&1" >> /etc/crontabs/root

CMD ["sh", "-c", "printenv > /etc/environment && crond -f -l 8"]

FROM python:3.9

WORKDIR /var/www/api.game-sense.net

VOLUME /var/www/api.game-sense.net

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--user", "root", "api:app"]
FROM python:3.9-slim

WORKDIR /app

RUN pip install --no-cache-dir pip-tools

COPY pyproject.toml .
RUN pip-compile pyproject.toml -o requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9000

ENV FLASK_RUN_HOST=0.0.0.0

RUN flask --app flaskr init-db

CMD ["flask", "--app", "flaskr", "run", "-p", "9000", "--debug"]
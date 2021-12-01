FROM python:3.9

WORKDIR /opt/app

COPY Pipfile.lock ./
COPY Pipfile ./
RUN pip install pipenv
RUN pipenv install --system

COPY aoc_bot/bot.py ./
COPY aoc_bot/models.py ./

CMD ["python", "bot.py"]

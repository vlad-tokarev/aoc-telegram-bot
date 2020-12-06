FROM python:3.9

WORKDIR /opt/app

COPY Pipfile.lock ./
RUN pip install pipenv && pipenv sync --system

COPY aoc_bot/bot.py ./
COPY aoc_bot/models.py ./

CMD ["python", "bot.py"]

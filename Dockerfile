FROM python:3.9

WORKDIR /opt/app

COPY Pipfile.lock ./
COPY Pipfile ./
RUN pip install pipenv
RUN pipenv install --system

COPY aoc_bot ./aoc_bot
ENV PYTHONPATH=/opt/app
CMD ["python", "aoc_bot/bot.py"]

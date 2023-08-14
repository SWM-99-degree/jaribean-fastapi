FROM python:3.10.10

WORKDIR /code

COPY ./requirement.txt /code/requirement.txt

COPY ./.env /code/.env
COPY ./jaribean-3af6f-firebase-adminsdk-voaca-c380f36f12.json /code/jaribean-3af6f-firebase-adminsdk-voaca-c380f36f12.json

RUN pip install --no-cache-dir -r /code/requirement.txt

COPY ./app /code/app

CMD uvicorn app.main:app --host 0.0.0.0 --port 3000

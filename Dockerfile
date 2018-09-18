FROM python:2.7-alpine

RUN apk add --no-cache gcc libc-dev libffi-dev openssl-dev

RUN mkdir /sudoisbot
WORKDIR /sudoisbot

COPY setup.py /sudoisbot
COPY README.md /sudoisbot
COPY bin /sudoisbot/bin
COPY sudoisbot /sudoisbot/sudoisbot

RUN pip install cffi && python setup.py install

COPY sudoisbot.yml /etc/sudoisbot.yml
ENTRYPOINT ["python", "/usr/local/bin/tglistener.py"]

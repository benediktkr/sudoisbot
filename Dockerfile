FROM python:2.7

RUN mkdir /sudoisbot
WORKDIR /sudoisbot

COPY setup.py /sudoisbot
COPY README.md /sudoisbot
COPY bin /sudoisbot/bin
COPY sudoisbot /sudoisbot/sudoisbot

RUN python setup.py install

COPY sudoisbot.yml /etc/sudoisbot.yml
ENTRYPOINT ["python", "/usr/local/bin/tglistener.py"]

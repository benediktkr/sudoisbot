FROM python:3.8
MAINTAINER Benedikt Kristinsson <benedikt@lokun.is>

ENV SUDOISBOT_VERSION "0.2.1"
COPY dist/sudoisbot-${SUDOISBOT_VERSION}.tar.gz /opt/sudoisbot.tar.gz

RUN pip install /opt/sudoisbot.tar.gz

# idea is to override with bind mounts
# since config.py doesnt do env vars as-is
ENV SUDOISBOT_CONF "/etc/sudoisbot.yml"

ENV SUDOISBOT_LOGFILE "/var/log/sudoisbot/sudoisbot.log"

EXPOSE 5559
EXPOSE 5560

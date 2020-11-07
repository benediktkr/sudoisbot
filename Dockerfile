FROM python:3.8
MAINTAINER Benedikt Kristinsson <benedikt@lokun.is>

COPY dist/sudoisbot-latest.tar.gz /opt/sudoisbot.tar.gz

# should build dependencies first
RUN pip install /opt/sudoisbot.tar.gz

# idea is to override with bind mounts
# since config.py doesnt do env vars as-is
ENV SUDOISBOT_CONF "/etc/sudoisbot.yml"
ENV SUDOISBOT_LOGFILE "/data/sudoisbot.log"

EXPOSE 5559
EXPOSE 5560

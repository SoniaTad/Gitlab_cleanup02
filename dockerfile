FROM python:3.11-slim

#LABEL org.opencontainers.image.source https://github.com//Gitlab_cleanup02
LABEL org.opencontainers.image.base.name python:3.11-slim
LABEL org.opencontainers.image.version 1.0


WORKDIR /python

COPY ./source /python

RUN pip install --no-cache-dir -r requirements.txt

ENV Token='' \
    GitlabHost='' \
    DryRun=''

RUN ln -sf /dev/stdout GC2.log

CMD [ "/usr/local/bin/python", "GC2.py"]

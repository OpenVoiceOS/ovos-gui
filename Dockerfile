FROM debian:buster-slim

RUN apt-get update && \
  apt-get install -y git python3 python3-dev python3-pip curl build-essential

COPY . /tmp/ovos-gui
RUN pip3 install /tmp/ovos-gui

ENTRYPOINT mycroft-gui-service
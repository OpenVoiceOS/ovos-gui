FROM ghcr.io/openvoiceos/core:dev

COPY . /tmp/ovos-gui
RUN pip3 install /tmp/ovos-gui

USER mycroft

ENTRYPOINT ovos-gui-service
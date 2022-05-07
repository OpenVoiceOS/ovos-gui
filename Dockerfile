FROM openvoiceos/core:dev

COPY . /tmp/ovos-gui
RUN pip3 install /tmp/ovos-gui

USER mycroft

ENTRYPOINT mycroft-gui-service
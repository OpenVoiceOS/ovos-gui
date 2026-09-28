# OVOS GUI MessageBus

`ovos-gui` is the GUI messagebus service for ovos-core. It manages GUI state and implements the [GUI protocol](./protocol.md).

GUI clients (the applications that draw the GUI) connect to this service over a websocket.

## Configuration

Configure the service under `mycroft.conf`.

```javascript
{
  "gui": {
    // Override: SYSTEM (set by specific enclosures)
    // Uncomment or add "idle_display_skill" to set the initial homescreen
    // "idle_display_skill": "skill-ovos-homescreen.openvoiceos",

    // Extensions are plugins that add GUI platform support for specific devices.
    // For example, set extension to "ovos-gui-plugin-shell-companion" if you use ovos-shell.
    "extension": "generic",

    // The default generic extension can provide homescreen functionality if enabled.
    "generic": {
        "homescreen_supported": false
    },

    // Optionally set a default QT version for connected clients that do not report one.
    // NOTE: currently only QT5 clients exist
    "default_qt_version": 5
  },

  // The GUI messagebus websocket. One port is created per connected GUI.
  "gui_websocket": {
    "host": "0.0.0.0",
    "base_port": 18181,
    "route": "/gui",
    "ssl": false
  }
}
```

## Plugins

Plugins add platform-specific GUI functionality, such as showing a homescreen or closing a window.

You usually do not need any of these plugins unless a GUI client application tells you to install one.

- [OpenVoiceOS/ovos-gui-plugin-shell-companion](https://github.com/OpenVoiceOS/ovos-gui-plugin-shell-companion)
- [OpenVoiceOS/ovos-gui-plugin-mobile](https://github.com/OpenVoiceOS/ovos-gui-plugin-mobile)
- [OpenVoiceOS/ovos-gui-plugin-plasmoid](https://github.com/OpenVoiceOS/ovos-gui-plugin-plasmoid)
- [OpenVoiceOS/ovos-gui-plugin-bigscreen](https://github.com/OpenVoiceOS/ovos-gui-plugin-bigscreen)

## Related projects

- [OpenVoiceOS/ovos-core](https://github.com/OpenVoiceOS/ovos-core) — the assistant runtime that this service runs alongside.
- [OpenVoiceOS/ovos-gui-api-client](https://github.com/OpenVoiceOS/ovos-gui-api-client) — a Python client library for this service.
- [OpenVoiceOS/ovos-shell](https://github.com/OpenVoiceOS/ovos-shell) — a reference GUI client that connects to this service.

## Limitations

Skills and other OVOS components populate GUI resource files under the local OVOS cache directory. GUI client applications must be able to reach these files.

This means a GUI client must run on the same machine as `ovos-gui`, or implement its own access to the resource files. Resolving page names to URIs is the responsibility of the client application.

> TODO: a new repository will host the removed GUI file server, to serve resource files from the cache directory to client apps.

In a container setup, mount a shared volume between `ovos-gui`, the skills service, and the GUI client apps.

## License

This project is licensed under the [Apache License 2.0](./LICENSE.md).

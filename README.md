# OVOS GUI MessageBus

GUI messagebus service, manages GUI state and implements the [gui protocol](./protocol.md)

GUI clients (the application that actually draws the GUI) connect to this service


# Configuration

under mycroft.conf

```javascript
{
  "gui": {
    // Override: SYSTEM (set by specific enclosures)
    // Uncomment or add "idle_display_skill" to set initial homescreen
    // "idle_display_skill": "skill-ovos-homescreen.openvoiceos",

    // Extensions are plugins that provide additional GUI platform support for specific devices
    // eg, if using ovos-shell you should set extension to "ovos-gui-plugin-shell-companion"
    "extension": "generic",

    // Default generic extension can provide homescreen functionality if enabled
    "generic": {
        "homescreen_supported": false
    },
    
    // Optionally specify a default qt version for connected clients that don't report it
    // NOTE: currently only QT5 clients exist
    "default_qt_version": 5
  },
  
  // The GUI messagebus websocket.  Once port is created per connected GUI
  "gui_websocket": {
    "host": "0.0.0.0",
    "base_port": 18181,
    "route": "/gui",
    "ssl": false
  }
}
```

# Plugins

plugins provide platform specific GUI functionality, such as determining when to show a homescreen or close a window

you should usually not need any of these unless instructed to install it from a GUI client application

- https://github.com/OpenVoiceOS/ovos-gui-plugin-shell-companion
- https://github.com/OpenVoiceOS/ovos-gui-plugin-mobile
- https://github.com/OpenVoiceOS/ovos-gui-plugin-plasmoid
- https://github.com/OpenVoiceOS/ovos-gui-plugin-bigscreen


# Limitations

gui resources files are populated under `~/.cache/mycrot/ovos-gui` by skills and other OVOS components and are expectd to be accessible by GUI client applications

This means GUI clients are expected to be running under the same machine or implement their own access to the resource files (resolving page names to uris is the client app responsibility)

> TODO: new repository with the removed GUI file server, serve files from `~/.cache/mycrot/ovos-gui` to be handled by client apps

In case of containers a shared volume should be mounted between ovos-gui, skills and gui client apps


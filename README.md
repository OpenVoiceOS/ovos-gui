# OVOS GUI MessageBus

GUI messagebus service, manages GUI state and implements the [gui protocol](./protocol.md)

GUI clients (the application that actually draws the GUI) connect to this service


# Plugins

plugins provide platform specific GUI functionality, such as determining when to show a homescreen or close a window

you should usually not need any of these unless instructed to install it from a GUI client application

- https://github.com/OpenVoiceOS/ovos-gui-plugin-shell-companion
- https://github.com/OpenVoiceOS/ovos-gui-plugin-mobile
- https://github.com/OpenVoiceOS/ovos-gui-plugin-plasmoid
- https://github.com/OpenVoiceOS/ovos-gui-plugin-bigscreen

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
    
    // Optional file server support for remote clients
    // "gui_file_server": true,
    // "file_server_port": 8000,
    
    // Optional support for collecting GUI files for container support
    // The ovos-gui container path for these files will be {XDG_CACHE_HOME}/ovos_gui_file_server.
    // With the below configuration, the GUI client will have files prefixed with the configured host path,
    // so the example below describes a situation where `{XDG_CACHE_HOME}/ovos_gui_file_server` maps
    // to `/tmp/gui_files` on the filesystem where the GUI client is running.    
    // "gui_file_host_path": "/tmp/gui_files",
    
    // Optionally specify a default qt version for connected clients that don't report it
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

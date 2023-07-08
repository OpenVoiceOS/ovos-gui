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

    // Extensions provide additional GUI platform support for specific devices
    // Currently supported devices: smartspeaker, bigscreen or generic
    "extension": "generic",

    // Generic extension can additionaly provide homescreen functionality
    // homescreen support is disabled by default for generic extension
    "generic": {
        "homescreen_supported": false
    }
    
    // Optional file server support for remote clients
    // "gui_file_server": true,
    // "file_server_port": 8000,
        
    // Optionally specify a default qt version for connected clients
    // "default_qt_version": 5,
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
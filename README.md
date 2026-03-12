# OVOS GUI MessageBus

**Template-based GUI system for OpenVoiceOS**

The GUI messagebus service manages GUI state and implements the standardized template protocol. GUI clients (Qt, web, etc.) connect to this service to receive data and display it.

---

## 📚 Documentation

**All documentation is in the [docs/](docs/) folder. Start here:**

- **[docs/index.md](docs/index.md)** — 📍 Complete documentation hub with navigation by role
- **[docs/getting-started/quick-start.md](docs/getting-started/quick-start.md)** — ⚡ 5-minute example (any developer)
- **[docs/getting-started/installation.md](docs/getting-started/installation.md)** — 📦 Installation & setup
- **[docs/skill-development/](docs/skill-development/)** — 🐍 For Python skill developers
- **[docs/adapter-development/](docs/adapter-development/)** — 🎨 For GUI adapter developers (Qt, web, etc.)
- **[docs/operations/](docs/operations/)** — 🔧 For system integrators & operators
- **[docs/development/](docs/development/)** — 🤝 For contributors

---

## Quick Links

- **Skill developer?** → [docs/skill-development/skill-gui-development.md](docs/skill-development/skill-gui-development.md)
- **Adapter developer?** → [docs/adapter-development/architecture.md](docs/adapter-development/architecture.md)
- **Want to contribute?** → [docs/development/contributing.md](docs/development/contributing.md)
- **Need help?** → [docs/faq.md](docs/faq.md) or [docs/operations/monitoring.md](docs/operations/monitoring.md)

---

## Configuration

**[Full configuration reference](docs/getting-started/installation.md)** — See docs for complete setup guide

Basic configuration in `mycroft.conf`:

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


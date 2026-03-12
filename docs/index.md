
# OVOS GUI — Developer Documentation

Welcome to the OVOS GUI system documentation. The GUI layer uses a **template-based adapter pattern** where skills define content via standardized data templates, and display adapters (Qt5, web, etc.) render them independently.

**Key concept**: Decoupled GUI rendering. Skills don't know about UI frameworks. Adapters don't know about skills. Communication happens via templates and the MessageBus.

---

## 📚 Documentation Organization

### Getting Started
- **[Quick Start](quick-start.md)** (5 min) — Minimal example: show weather on any display
- **[Installation & Setup](installation.md)** — Installing ovos-gui and adapters
- **[Core Concepts](concepts.md)** — Namespaces, templates, adapters, MessageBus communication

### For Skill Developers
- **[Skill GUI Development](skill-gui-development.md)** — Using `self.gui.*` template methods in your skill
- **[Skill Examples](skill-examples.md)** — Real-world examples: weather, music, news
- **[Template API Reference](templates.md)** — All 21 templates with data keys
- **[Advanced: Session State](advanced-state.md)** — Managing persistent data across pages
- **[Testing GUI Functionality](testing-gui.md)** — Unit and integration tests for GUI features

### For Adapter Developers
- **[Adapter Plugin System](adapter-plugins.md)** — Writing custom GUI adapters
- **[Qt5 Adapter Guide](adapting-qt5.md)** — Deep dive: the Qt5 adapter implementation
- **[QML Patterns & Components](qml-components.md)** — Reusable QML patterns
- **[Bus Protocol Reference](bus-protocol.md)** — MessageBus API and events

### System Architecture
- **[Architecture Overview](architecture.md)** — How skills, templates, adapters, and the MessageBus interact
- **[Legacy Qt Plugin](legacy-qt-plugin.md)** — Historical context for `ovos-legacy-mycroft-gui-plugin`
- **[Skill Migration Guide](skill-migration.md)** — Migrating from old `show_page()` to template API

### Operations & Troubleshooting
- **[Performance Optimization](performance.md)** — Tuning for embedded devices and high-latency networks
- **[Monitoring & Debugging](monitoring.md)** — Logging, debugging tools, troubleshooting
- **[Glossary](glossary.md)** — Terminology reference
- **[Contributing Guide](contributing.md)** — Contributing to ovos-gui

---

## 🎯 Quick Start by Role

### I'm a skill developer (Python)
1. Read: **[Skill GUI Development](skill-gui-development.md)**
2. Look up template methods: **[Templates.md](templates.md)** (search by data type, e.g., "weather")
3. See examples: **[Skill Examples](skill-examples.md)**
4. Test: **[Testing Guide](testing-gui.md)**

### I'm a GUI adapter developer
1. Read: **[Architecture](architecture.md)** to understand the design
2. Follow: **[Adapter Plugin System](adapter-plugins.md)** for entry points and lifecycle
3. If building Qt-based: **[Qt5 Adapter Guide](adapting-qt5.md)** + **[QML Patterns](qml-components.md)**
4. Reference: **[Bus Protocol](bus-protocol.md)** for all MessageBus events
5. Debug: **[Monitoring & Debugging](monitoring.md)**

### I'm an OVOS maintainer or integrator
1. Read: **[Architecture](architecture.md)** for the big picture
2. See: **[Performance Guide](performance.md)** for tuning
3. Monitor: **[Monitoring Guide](monitoring.md)** for production deployments
4. Contribute: **[Contributing Guide](contributing.md)**

---

## 📋 Complete Reference

| Document | Audience | Purpose |
|----------|----------|---------|
| **Quick Start** | Everyone | 5-minute hands-on example |
| **Installation** | Skill devs, integrators | Setting up ovos-gui and adapters |
| **Core Concepts** | Everyone | Key terminology and mental models |
| **Skill GUI Development** | Skill devs | Using templates in skills |
| **Skill Examples** | Skill devs | Copy-paste examples |
| **Templates** | Everyone | Data schema for all 21 templates |
| **Advanced: Session State** | Skill devs | Persistent data, lifecycle |
| **Testing GUI** | Skill devs | Unit and integration tests |
| **Adapter System** | Adapter devs | Plugin architecture and lifecycle |
| **Qt5 Adapter Guide** | Adapter devs (Qt/C++) | Deep-dive implementation |
| **QML Patterns** | Adapter devs (QML) | Reusable QML components |
| **Bus Protocol** | Adapter devs | All MessageBus events |
| **Architecture** | Tech leads | System design and motivation |
| **Legacy Qt Plugin** | Maintainers | Historical context |
| **Skill Migration** | Maintainers, legacy skills | Upgrading from old API |
| **Performance** | Integrators | Tuning for embedded |
| **Monitoring** | Operators | Logging, debugging, production support |
| **Glossary** | Reference | Terminology |
| **Contributing** | Contributors | Code style, pull request process |

---

## 🔑 Key Concepts (TL;DR)

### Template-Based Architecture
Skills don't create custom QML or HTML. Instead, they call standardized template methods:

```python
# Skill code
self.gui.show_weather(current_temp=22, condition="Cloudy", location="Berlin")
```

The GUI service translates this into a **namespace** with a **page** containing the template data. Any connected **adapter** (Qt5, web, etc.) listens on the MessageBus and renders it.

### Namespaces & Pages
- **Namespace**: A logical "window" for a skill or component (e.g., `skill-weather.openvoiceos`, `system`)
- **Page**: A single screen or view within that namespace (e.g., `forecast`, `current`)
- **Session**: Temporary state shared between skill and adapter (e.g., user selections, scroll position)

### Adapters
An adapter is a GUI renderer plugin that:
1. Listens for GUI events on the MessageBus
2. Receives template data (JSON)
3. Renders it in its own framework (Qt, HTML, terminal, etc.)
4. Sends user interactions back to the skill via MessageBus

### MessageBus
All communication flows through the OVOS MessageBus (WebSocket pub/sub):
- Skills → GUI service: `gui.request_page` (show a template)
- GUI service → Adapters: `gui.page_show` (render this data)
- Adapters → Skills: `gui.user_input` (user clicked a button)

---

## 📖 Learn More

- **OVOS Core Documentation**: [docs.openvoiceos.com](https://docs.openvoiceos.com)
- **Skill Development Workshop**: [ovos-workshop on GitHub](https://github.com/OpenVoiceOS/ovos-workshop)
- **Community Forum**: [OpenVoiceOS Community](https://openvoiceos.com/forum)
- **GitHub**: [OpenVoiceOS/ovos-gui](https://github.com/OpenVoiceOS/ovos-gui)

---

## 📞 Need Help?

- **Bug report**: [GitHub Issues](https://github.com/OpenVoiceOS/ovos-gui/issues)
- **Feature request**: [GitHub Discussions](https://github.com/OpenVoiceOS/ovos-gui/discussions)
- **Question**: Post in the [Community Forum](https://openvoiceos.com/forum)

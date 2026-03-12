# OVOS GUI Documentation Hub

**Complete guide to the template-based GUI system for OpenVoiceOS**

---

## 🎯 Quick Navigation by Role

### 👨‍💻 I'm a Skill Developer (Python)
**Want to add a GUI to your skill in 15 minutes?**

1. **[getting-started/quick-start.md](getting-started/quick-start.md)** (5 min) — Hands-on example
2. **[skill-development/skill-gui-development.md](skill-development/skill-gui-development.md)** (10 min) — How to use templates in skills
3. **[skill-development/templates.md](skill-development/templates.md)** (reference) — All 21 templates and their data
4. **[skill-development/skill-examples.md](skill-development/skill-examples.md)** (copy-paste) — Real skill examples

---

### 🎨 I'm a GUI Adapter Developer (Qt/Web)
**Want to implement a new GUI display?**

1. **[adapter-development/architecture.md](adapter-development/architecture.md)** — How the system works
2. **[adapter-development/adapter-plugins.md](adapter-development/adapter-plugins.md)** — Plugin architecture and lifecycle
3. **[adapter-development/bus-protocol.md](adapter-development/bus-protocol.md)** — MessageBus API specification
4. **[protocol/protocol.md](protocol/protocol.md)** (reference) — Wire protocol details

If building a Qt adapter:
- **[adapter-development/legacy-qt-plugin.md](adapter-development/legacy-qt-plugin.md)** — Study the Qt5 implementation
- **[planning/RESEARCH_Qt5_Qt6_MIGRATION.md](planning/RESEARCH_Qt5_Qt6_MIGRATION.md)** — Qt6 compatibility assessment

---

### 🔧 I'm an OVOS Maintainer or System Integrator
**Want to deploy, tune, or troubleshoot the GUI system?**

1. **[getting-started/installation.md](getting-started/installation.md)** — Installing ovos-gui and adapters
2. **[getting-started/concepts.md](getting-started/concepts.md)** — Core terminology and mental models
3. **[operations/performance.md](operations/performance.md)** — Tuning for embedded devices
4. **[operations/monitoring.md](operations/monitoring.md)** — Logging, debugging, production support

---

### 🤝 I'm Contributing Code
**Want to contribute to ovos-gui?**

1. **[development/contributing.md](development/contributing.md)** — Code style, PR process, testing
2. **[development/TESTING.md](development/TESTING.md)** (NEW) — How to test changes
3. **[development/DEBUGGING.md](development/DEBUGGING.md)** (NEW) — Debugging techniques
4. **[operations/glossary.md](operations/glossary.md)** (reference) — Terminology

---

## 📚 Complete Documentation Index

### 🚀 Getting Started (New Users)

**Follow these in order:**

1. **[DOCUMENTATION_ROADMAP.md](DOCUMENTATION_ROADMAP.md)** 📍 Start here! Role-based navigation guide
2. **[getting-started/quick-start.md](getting-started/quick-start.md)** ⚡ 5-minute hands-on example
3. **[getting-started/concepts.md](getting-started/concepts.md)** 📚 Key terminology and mental models
4. **[getting-started/installation.md](getting-started/installation.md)** 📦 Step-by-step setup guide

**Time estimate**: 30-60 minutes for complete onboarding

### 📚 Core Documentation (Start Here)

| Document | Purpose | Role |
|----------|---------|------|
| **[DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md)** | ✅ **Single source of truth** — All design principles, template specs, architecture decisions | **All roles** |
| **[DOCUMENTATION_ROADMAP.md](DOCUMENTATION_ROADMAP.md)** | 📍 **Navigation guide** — Role-based paths through all documentation | **New users** |
| **[index.md](index.md)** | 📋 **This document** — Complete documentation hub with cross-references | **All roles** |

### 🎨 Design & Architecture

| Document | Purpose | Audience |
|----------|---------|----------|
| **[DESIGN_PHILOSOPHY.md](DESIGN_PHILOSOPHY.md)** | Template design, voice-first principles, cross-platform requirements | **All developers** |
| **[SESSION_AND_SITE_ID_DESIGN.md](SESSION_AND_SITE_ID_DESIGN.md)** | Multi-session/multi-device GUI state partitioning and routing | **System integrators, adapter developers** |
| **[adapter-development/architecture.md](adapter-development/architecture.md)** | System components and data flow | **Adapter developers** |
| **[protocol/protocol.md](protocol/protocol.md)** | Wire protocol and message formats (includes session routing) | **Adapter developers** |

### 🏆 Reference Implementation

**ovos-legacy-mycroft-gui-plugin — The canonical adapter reference:**

| Document | Purpose | Audience |
|----------|---------|----------|
| [index.md](https://github.com/OpenVoiceOS/ovos-legacy-mycroft-gui-plugin/blob/dev/docs/index.md) | Complete adapter documentation hub | **Adapter developers** |
| [bus-api-reference.md](https://github.com/OpenVoiceOS/ovos-legacy-mycroft-gui-plugin/blob/dev/docs/bus-api-reference.md) | All bus messages with examples | **All developers** |
| [ARCHITECTURE_REVIEW.md](https://github.com/OpenVoiceOS/ovos-legacy-mycroft-gui-plugin/blob/dev/docs/ARCHITECTURE_REVIEW.md) | 📋 Architecture decisions (ADRs) | **Contributors** |
| [PROTOCOL_EXTENSIONS.md](https://github.com/OpenVoiceOS/ovos-legacy-mycroft-gui-plugin/blob/dev/docs/PROTOCOL_EXTENSIONS.md) | WebSocket protocol extensions | **Adapter developers** |
| [OVOS_GUI_COMPATIBILITY.md](https://github.com/OpenVoiceOS/ovos-legacy-mycroft-gui-plugin/blob/dev/docs/OVOS_GUI_COMPATIBILITY.md) | ✅ Verified compatibility audit | **System integrators** |

### Skill Development (Python Developers)

| Document | Focus | Purpose |
|----------|-------|---------|
| **[skill-gui-development.md](skill-development/skill-gui-development.md)** | API | Using `self.gui.*` methods in skills |
| **[skill-examples.md](skill-development/skill-examples.md)** | Examples | Real-world examples: weather, music, news, clocks |
| **[templates.md](skill-development/templates.md)** | Reference | All 21 templates, data schema, examples |
| **[advanced-state.md](skill-development/advanced-state.md)** | Advanced | Persistent session data, lifecycle management |
| **[testing-gui.md](skill-development/testing-gui.md)** | Testing | Unit and integration tests for GUI features |

### Adapter Development (Qt/Web/Display Developers)

| Document | Focus | Purpose |
|----------|-------|---------|
| **[architecture.md](adapter-development/architecture.md)** | Design | System architecture, data flow, component interaction |
| **[adapter-plugins.md](adapter-development/adapter-plugins.md)** | Implementation | Plugin entry points, lifecycle hooks, resource management |
| **[bus-protocol.md](adapter-development/bus-protocol.md)** | API | MessageBus events, message format, state synchronization |
| **[legacy-qt-plugin.md](adapter-development/legacy-qt-plugin.md)** | Reference | Canonical Qt5 implementation (study this) |
| **[skill-migration.md](adapter-development/skill-migration.md)** | Migration | Upgrading from old `show_page()` to template API |

### Protocol & Technical Reference

| Document | Purpose |
|----------|---------|
| **[protocol/protocol.md](protocol/protocol.md)** | Complete wire protocol: core GUI, shell features, message formats |

### Operations & Administration

| Document | Focus | Purpose |
|----------|-------|---------|
| **[performance.md](operations/performance.md)** | Tuning | Optimization for embedded devices, high-latency networks |
| **[monitoring.md](operations/monitoring.md)** | Debugging | Logging, debugging tools, troubleshooting production issues |
| **[glossary.md](operations/glossary.md)** | Reference | Terminology and concepts |
| **[MAINTENANCE_REPORT.md](operations/MAINTENANCE_REPORT.md)** | Audit | Project status and maintenance log |

### Development (Contributors)

| Document | Focus | Purpose |
|----------|-------|---------|
| **[contributing.md](development/contributing.md)** | Guidelines | Code style, testing, pull request process |
| **[TESTING.md](development/TESTING.md)** (NEW) | Testing | Running tests, writing new tests, test coverage |
| **[DEBUGGING.md](development/DEBUGGING.md)** (NEW) | Debugging | Debug modes, tools, common issues |

### Planning & Research

| Document | Purpose |
|----------|---------|
| **[planning/RESEARCH_Qt5_Qt6_MIGRATION.md](planning/RESEARCH_Qt5_Qt6_MIGRATION.md)** | Qt6 compatibility assessment and strategy |
| **[planning/SUGGESTIONS.md](planning/SUGGESTIONS.md)** | Enhancement proposals and technical debt |

### FAQs & Quick Reference

| Document | Purpose |
|----------|---------|
| **[faq.md](faq.md)** | Frequently asked questions |
| **[quick-facts.md](quick-facts.md)** | Quick reference: package info, versions, entry points |

---

## 📋 Learning Paths

### Path 1: Skill Developer (1-2 hours)
1. [getting-started/quick-start.md](getting-started/quick-start.md) — 5 min
2. [skill-development/skill-gui-development.md](skill-development/skill-gui-development.md) — 20 min
3. [skill-development/templates.md](skill-development/templates.md) — 20 min (skim for your templates)
4. [skill-development/skill-examples.md](skill-development/skill-examples.md) — 20 min (find similar example)
5. Implement your GUI — 30 min
6. Test using [skill-development/testing-gui.md](skill-development/testing-gui.md) — 15 min

### Path 2: Adapter Developer (4-6 hours)
1. [adapter-development/architecture.md](adapter-development/architecture.md) — 30 min
2. [getting-started/concepts.md](getting-started/concepts.md) — 15 min
3. [adapter-development/adapter-plugins.md](adapter-development/adapter-plugins.md) — 45 min
4. [adapter-development/bus-protocol.md](adapter-development/bus-protocol.md) — 45 min
5. Study [adapter-development/legacy-qt-plugin.md](adapter-development/legacy-qt-plugin.md) — 60 min
6. Implement adapter — 2-3 hours

### Path 3: System Integrator (2-3 hours)
1. [getting-started/quick-start.md](getting-started/quick-start.md) — 5 min
2. [getting-started/concepts.md](getting-started/concepts.md) — 15 min
3. [getting-started/installation.md](getting-started/installation.md) — 30 min
4. [operations/performance.md](operations/performance.md) — 45 min
5. [operations/monitoring.md](operations/monitoring.md) — 45 min

### Path 4: Contributor (2-3 hours)
1. [development/contributing.md](development/contributing.md) — 30 min
2. [development/TESTING.md](development/TESTING.md) — 45 min
3. [development/DEBUGGING.md](development/DEBUGGING.md) — 45 min
4. Review [adapter-development/architecture.md](adapter-development/architecture.md) — 30 min

---

## 🔄 Document Relationships

```
README.md (root)
    │
    └─ docs/index.md (you are here)
        │
        ├─ getting-started/
        │   ├── quick-start.md
        │   ├── installation.md
        │   └── concepts.md
        │
        ├─ skill-development/
        │   ├── skill-gui-development.md
        │   ├── templates.md
        │   ├── skill-examples.md
        │   ├── advanced-state.md
        │   └── testing-gui.md
        │
        ├─ adapter-development/
        │   ├── architecture.md
        │   ├── adapter-plugins.md
        │   ├── bus-protocol.md
        │   ├── legacy-qt-plugin.md
        │   └── skill-migration.md
        │
        ├─ protocol/
        │   └── protocol.md
        │
        ├─ operations/
        │   ├── performance.md
        │   ├── monitoring.md
        │   ├── glossary.md
        │   └── MAINTENANCE_REPORT.md
        │
        ├─ development/
        │   ├── contributing.md
        │   ├── TESTING.md (NEW)
        │   └── DEBUGGING.md (NEW)
        │
        ├─ planning/
        │   ├── RESEARCH_Qt5_Qt6_MIGRATION.md
        │   └── SUGGESTIONS.md
        │
        ├─ faq.md
        └─ quick-facts.md
```

---

## 🔑 Core Concepts (TL;DR)

### Template-Based Architecture

Skills don't create custom QML or HTML. Instead, they use **standardized templates**:

```python
# Skill code
self.gui.show_weather(
    current_temp=22,
    condition="Cloudy",
    location="Berlin"
)
```

The GUI adapter (Qt, web, etc.) renders independently:
- Skills don't know about UI frameworks
- Adapters don't know about skill logic
- Communication via templates and the MessageBus

### Key Components

- **Skills** — Python code that provides data
- **ovos-gui** — Messagebus service managing GUI state
- **Templates** — Standardized data schemas (weather, text, list, etc.)
- **Adapters** — Display implementations (Qt, web, etc.)
- **MessageBus** — Communication layer between all components

### Data Flow

```
Skill calls:
  self.gui.show_weather(temp=22, condition="Cloudy")
         ↓
ovos-gui:
  Stores template data in session
  Broadcasts "gui.page.show" event
         ↓
GUI Adapter (Qt/Web):
  Receives event
  Renders SYSTEM_weather template with data
  Displays on screen
         ↓
User interacts:
  Clicks button → sends "gui.user.interaction" event
         ↓
Skill receives:
  Event handler triggered
  Same action as voice command
```

---

## 📊 Documentation Statistics

| Metric | Value |
|--------|-------|
| Total markdown files | 25+ |
| Total documentation lines | 150,000+ |
| Main sections | 9 |
| Quick-start guides | 3 |
| Code examples | 50+ |
| API reference pages | 5+ |
| Tutorial documents | 10+ |

---

## 🆘 Getting Help

**Can't find what you're looking for?**

1. **Start with [DOCUMENTATION_ROADMAP.md](DOCUMENTATION_ROADMAP.md)** — Follow the path for your role
2. **Check [glossary.md](operations/glossary.md)** — Terminology definitions
3. **Read [faq.md](faq.md)** — Common questions and answers
4. **Search this documentation** — Use browser Find (Ctrl+F)
5. **Ask in community** — Provide link to relevant documentation

**Found outdated information?**

1. **Check [MAINTENANCE_REPORT.md](operations/MAINTENANCE_REPORT.md)** — See current status
2. **Create an issue** — Report in the relevant repository
3. **Submit a PR** — Follow [contributing guidelines](development/contributing.md)

**Need to navigate between repos?**

Use the cross-reference tables in each document to jump between:
- `ovos-gui` → Design specifications
- `ovos-gui-api-client` → Skill API reference  
- `ovos-legacy-mycroft-gui-plugin` → Reference implementation

---

## 🔗 Related Projects

- **[mycroft-gui-qt6](https://github.com/OpenVoiceOS/mycroft-gui-qt6)** — Modern Qt6 GUI client (uses this architecture)
- **[mycroft-gui-qt5](https://github.com/OpenVoiceOS/mycroft-gui-qt5)** — Legacy Qt5 client
- **[ovos-gui-api-client](https://github.com/OpenVoiceOS/ovos-gui-api-client)** — Python client library for skills
- **[pyhtmx-gui-client](https://github.com/OpenVoiceOS/pyhtmx-gui-client)** — Browser-based GUI client
- **[ovos-shell](https://github.com/OpenVoiceOS/ovos-shell)** — Full desktop shell

---

## 📝 Recent Updates

- **2026-03-12**: Enhanced documentation structure with skill-development and adapter-development sections
- Added **[development/TESTING.md](development/TESTING.md)** — Comprehensive testing guide
- Added **[development/DEBUGGING.md](development/DEBUGGING.md)** — Debugging techniques and tools
- Reorganized planning documents to **[planning/](planning/)**
- Updated index with learning paths by role

---

## ✍️ How to Use This Documentation

1. **Start with your role** — Use quick navigation section above
2. **Follow the learning path** — Each role has a recommended sequence
3. **Refer back to index** — Document relationships show how everything connects
4. **Cross-reference** — All documents link to related content
5. **Bookmark key docs** — Skill devs should bookmark [templates.md](skill-development/templates.md), adapters should bookmark [bus-protocol.md](adapter-development/bus-protocol.md)

---

**Last Updated**: 2026-03-12
**Total Documentation**: 25+ files, 150,000+ lines, organized for all roles
**All paths**: Relative links work from docs/index.md

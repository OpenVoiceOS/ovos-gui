# GUI System Overhaul — Implementation Plan

**Status**: In Progress (Phase 4)
**Date**: 2026-03-12
**Scope**: ovos-gui documentation, testing, CI fixes, and Qt5→Qt6 migration planning

---

## Executive Summary

The OVOS GUI system (ovos-gui + adapters) underwent a **template-based adapter refactor** to support multiple client frameworks (Qt5, Qt6, PyHTMX). This plan addresses four critical areas:

1. **Testing** (A1–A3): Improve unit test coverage from 0% to ≥85%
2. **Qt5→Qt6 Migration** (B1–B3): Plan and document migration path
3. **CI/CD** (A3): Fix Python version matrix and pin action versions
4. **Documentation** (A2, C1–C2): Enrich suggestions and create implementation tracker

---

## Current State

### Architecture
- **Core**: `ovos-gui` (NamespaceManager, Namespace, GuiPage)
- **Client API**: `ovos-gui-api-client` (GUIInterface with 21 template methods)
- **Adapters**:
  - `ovos-legacy-mycroft-gui-plugin` (Qt5/Tornado)
  - `pyhtmx-gui-client` (Browser/FastAPI)
- **Desktop Clients**:
  - `mycroft-gui-qt5` (C++/QML, Plasma Bigscreen)
  - `mycroft-gui-qt6` (Newer Qt6 version)

### Known Issues
1. ✅ Docs exist but are auto-generated (SUGGESTIONS.md lacks evidence-based proposals)
2. ❌ Unit tests: only ~30% coverage (17 tests passing out of 49)
3. ❌ CI: Python 3.9 (deprecated), 3.11 pinned, actions unpinned
4. ❓ Qt5→Qt6 migration path not documented

---

## Implementation Tasks

### PART A: Testing & Documentation

#### **A1: Complete Unit Tests** (HIGH PRIORITY)
- **Status**: In Progress
- **Work**: Implement missing test methods in `test/unittests/test_namespace.py`
- **Current**: 30% coverage (17 tests passing)
- **Target**: ≥85% coverage
- **Methods Implemented**:
  - `test_validate_page_message()` — message validation
  - `test_get_idle_display_config()` — idle screen handling
  - `test_get_active_gui_extension()` — active page retrieval
  - `test_unload_data()` — data removal
  - `test_page_gained_focus()` — page focus updates
  - `test_global_back()` — back navigation
  - Plus 20+ NamespaceManager handler tests
- **Remaining**: Fix integration tests, refine mock usage

#### **A2: Enrich SUGGESTIONS.md** (MEDIUM PRIORITY)
- **Status**: Pending (depends on A1 coverage report)
- **Work**: Replace auto-generated suggestions with evidence-based proposals
- **Format**: `file.py:LINE — [Type] Description`
- **Target**: ≥3 specific, actionable suggestions

#### **A3: Fix CI Matrix** (MEDIUM PRIORITY)
- **Status**: ✅ COMPLETED
- **Work Done**:
  - ✅ Pinned `actions/checkout@v4`, `actions/setup-python@v5`
  - ✅ Updated Python 3.9 → 3.11
  - ✅ Removed deprecated env vars
  - ✅ Converted `pip` → `uv pip`

---

### PART B: Qt5→Qt6 Migration (Research Only)

#### **B1: Audit Qt5 vs Qt6** (MEDIUM PRIORITY)
- **Status**: Pending (agent researching)
- **Scope**: Identify compatibility breaking changes
- **Deliverable**: Migration checklist (markdown)
- **Key Areas**:
  - QML syntax differences
  - C++ API changes (signals/slots, property bindings)
  - CMake configuration changes
  - QML component compatibility

#### **B2: Adapter Compatibility** (MEDIUM PRIORITY)
- **Status**: Pending (depends on B1)
- **Work**: Determine if current adapter (ovos-legacy-mycroft-gui-plugin) works with Qt6
- **Deliverable**: Compatibility matrix (yes/no + reasoning)

#### **B3: Rollout Strategy** (MEDIUM PRIORITY)
- **Status**: Pending (depends on B1, B2)
- **Options to Evaluate**:
  - **Option A**: Parallel support (adapter handles both Qt5 and Qt6)
  - **Option B**: Adapter versioning (v1.x for Qt5, v2.x for Qt6)
  - **Option C**: Feature flags (config toggle)
  - **Option D**: Hard cutover (drop Qt5 support)
- **Deliverable**: Recommendation with trade-offs and risk assessment

---

### PART C: Deliverables (LOW PRIORITY)

#### **C1: PLAN.md** (This File)
- ✅ STARTED
- Executive summary and context
- Implementation tasks with effort/priority
- Dependencies and success criteria

#### **C2: TODO.md**
- **Status**: Pending
- Task tracking for ongoing work
- Checkbox list format

---

## Critical Files to Modify

| File | Changes | Status |
|------|---------|--------|
| `ovos-gui/test/unittests/test_namespace.py` | Add 25+ test implementations | ✅ In Progress |
| `ovos-gui/SUGGESTIONS.md` | Replace auto-gen with evidence-based | Pending |
| `.github/workflows/coverage.yml` | Pin actions, update Python | ✅ Done |
| `mycroft-gui-qt{5,6}/` | Audit only (read-only) | Pending |

---

## Execution Model

### Parallel Tasks
- **A-tasks** (testing, docs, CI) can run sequentially
- **B-tasks** (Qt6 research) can run in parallel with A-tasks

### Dependency Graph
```
A1 (tests) ──→ A2 (suggestions)
                ↓
A3 (CI) ────────+

B1 (Qt5 audit) ──→ B2 (adapter) ──→ B3 (rollout)
```

---

## Success Criteria

| Task | Criteria |
|------|----------|
| A1 | ≥85% coverage, all TODO tests resolved, tests pass |
| A2 | ≥3 specific suggestions with file:LINE citations |
| A3 | CI passes on dev/master, actions pinned |
| B1 | ≥5 compatibility issues documented with file paths |
| B2 | Clear yes/no on dual support with reasoning |
| B3 | Recommended strategy + risk assessment |
| C1 | PLAN.md written and committed |
| C2 | TODO.md written with checkbox list |

---

## Timeline & Effort Estimates

| Phase | Tasks | Est. Effort | Status |
|-------|-------|------------|--------|
| **1** | A1, B1 (parallel) | 3-4 hours | In Progress |
| **2** | A2, B2 (depends on 1) | 2-3 hours | Pending |
| **3** | A3 | 30 min | ✅ Done |
| **4** | B3 (depends on 1, 2) | 1 hour | Pending |
| **5** | C1, C2 | 1 hour | ✅ C1 Started |

**Total**: ~10-11 hours
**Current Progress**: A1 + A3 + C1 in progress

---

## Key Architectural Patterns

- **GUI Routing**: Template-based dispatch to adapters (SYSTEM_* pages)
- **Namespace Stack**: LIFO stack for active GUI namespaces
- **Session Routing**: Configurable via session_id / site_id
- **Plugin System**: Adapters loaded via OVOSPluginManager

---

## Notes for Implementation

1. **Test coverage**: Use `--cov-report=html` for visual inspection
2. **Type hints**: Mandatory per AGENTS.md
3. **Qt6 migration**: Defer code changes — this is research/planning only
4. **Documentation**: All suggestions must cite `file.py:LINE`
5. **Commits**: Prepare locally; human pushes to GitHub

---

## References

- [ovos-gui/docs/index.md](docs/index.md) — Architecture and API overview
- [GUI_DESIGN.md](GUI_DESIGN.md) — Template adapter specification
- [AGENTS.md](/home/miro/PycharmProjects/CLAUDE.md) — Workspace CI/CD standards

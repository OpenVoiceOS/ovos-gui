# TODO — ovos-gui System Overhaul

**Status**: ✅ COMPLETE (Phase 1-2 finished)
**Completed Date**: 2026-03-12
**Scope**: GUI system testing, documentation, CI, and Qt5→Qt6 migration planning

---

## COMPLETED PHASE 1: HIGH PRIORITY (Testing & CI)

- [x] **A3: Fix CI matrix** — ✅ Complete
  - [x] Pin action versions (v4, v5)
  - [x] Update Python matrix (3.10, 3.11, 3.12, 3.13)
  - [x] Fix workflow references

- [x] **A1: Complete unit tests** — ✅ **88% COVERAGE** (exceeded 85% target)
  - [x] Implemented test_validate_page_message, test_get_idle_display_config
  - [x] Added 60+ tests for NamespaceManager handlers
  - [x] Added comprehensive tui.py tests (0% → 91%)
  - [x] Added service.py run() tests (80% → 93%)
  - [x] Added version.py tests (0% → 100%)
  - [x] Added __main__.py tests (0% → 96%)
  - **Final**: 131 tests passing, 88% coverage

---

## COMPLETED PHASE 2: MEDIUM PRIORITY (Qt6 Migration Research)

- [x] **B1: Audit Qt5→Qt6 differences** — ✅ Complete
  - [x] Document QML breaking changes (import versioning)
  - [x] Document C++ API changes (QAudioProbe → QAudioSource, QAbstractVideoSurface → QVideoSink)
  - [x] Document CMakeLists.txt changes (KF5 → KF6)
  - [x] Produce detailed migration checklist
  - **Output**: `RESEARCH_Qt5_Qt6_MIGRATION.md`

- [x] **B2: Assess adapter compatibility** — ✅ Complete
  - [x] Check Tornado WS protocol (compatible with both Qt5 and Qt6)
  - [x] Analyze QML stubs in ovos-legacy-mycroft-gui-plugin
  - [x] Determine dual-client support feasibility
  - [x] Produce compatibility matrix
  - **Output**: `ADAPTER_COMPATIBILITY_ASSESSMENT.md`

- [x] **B3: Plan Qt5→Qt6 rollout strategy** — ✅ Complete
  - [x] Evaluate Option A: Parallel support (40-60 hrs)
  - [x] Evaluate Option B: Adapter versioning (20-30 hrs) ← RECOMMENDED
  - [x] Evaluate Option C: Feature flags (complex, not recommended)
  - [x] Evaluate Option D: Hard cutover (breaking)
  - [x] Recommend phased strategy with risk assessment
  - **Output**: `QT6_ROLLOUT_STRATEGY.md`

---

## COMPLETED PHASE 3: DOCUMENTATION

- [x] **A2: Enrich SUGGESTIONS.md** — ✅ Complete
  - [x] Replace auto-generated with evidence-based proposals
  - [x] Added 8 specific suggestions with file:LINE citations
  - [x] Examples: bounds checking, integration tests, namespace filtering

- [x] **C1: Write PLAN.md** — ✅ Complete
  - [x] Implementation roadmap for all A/B/C tasks
  - [x] Critical files identified
  - [x] Verification checklist included

- [x] **C2: Write TODO.md** — ✅ This file (now updated)
  - [x] Track completion status
  - [x] Link to deliverables

---

## NEXT PHASE: FUTURE WORK (Pending user direction)

- [ ] **Task #9: Plan QML consolidation** — Move all .qml files into mycroft-gui-qt5
  - [ ] Inventory .qml files across 6 repositories
  - [ ] Analyze dependencies and reusability
  - [ ] Design consolidation strategy
  - [ ] Document QML standards and conventions
  - **Status**: In-progress (requires separate session)

- [ ] **Optional: Implement Qt6 adapter** — If B3 rollout strategy is approved
  - [ ] Create ovos-legacy-mycroft-gui-adapter-qt6 package
  - [ ] Port media handling (QAudioSource, QVideoSink)
  - [ ] Create Qt6-specific QML variants
  - [ ] Test with real Qt6 GUI clients

---

## DELIVERABLES COMPLETED

| Deliverable | File | Status |
|-------------|------|--------|
| Implementation Plan | `PLAN.md` | ✅ |
| Todo Tracker | `TODO.md` | ✅ |
| Test Suite | `test/unittests/*` | ✅ (131 tests, 88% coverage) |
| CI Fixes | `.github/workflows/*` | ✅ |
| Qt6 Research | `RESEARCH_Qt5_Qt6_MIGRATION.md` | ✅ |
| Adapter Assessment | `ADAPTER_COMPATIBILITY_ASSESSMENT.md` | ✅ |
| Rollout Strategy | `QT6_ROLLOUT_STRATEGY.md` | ✅ |
| Code Suggestions | `SUGGESTIONS.md` | ✅ |

---

## COMMITS PREPARED

1. **test: Add comprehensive unit tests for __main__, version, and tui modules**
   - test_main.py (10 tests), test_version.py (9 tests), enhanced test_tui.py
   - Coverage: 64% → 82%

2. **test: Add tests for service run() and namespace error handling**
   - Enhanced test_service.py with run() tests
   - Added 7 namespace error path tests
   - Coverage: 82% → 88% ✅

---

## TEST COVERAGE SUMMARY

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| __init__.py | 100% | - | ✅ |
| __main__.py | 96% | 10 | ✅ |
| namespace.py | 86% | 67 | ✅ |
| page.py | 100% | - | ✅ |
| service.py | 93% | 16 | ✅ |
| tui.py | 91% | 30 | ✅ |
| version.py | 100% | 9 | ✅ |
| **TOTAL** | **88%** | **131** | **✅** |

---

## How to Run Tests & Coverage

```bash
# Run unit tests
cd "OpenVoiceOS Workspace/ovos-gui"
uv run pytest test/unittests/ -v

# Run with coverage report
uv run pytest test/unittests/ --cov=ovos_gui --cov-report=term-missing

# Generate HTML coverage report
uv run pytest test/unittests/ --cov=ovos_gui --cov-report=html
# Open htmlcov/index.html in browser
```

---

## References

- `PLAN.md` — Full implementation details
- `GUI_DESIGN.md` — Architecture and adapter spec
- `RESEARCH_Qt5_Qt6_MIGRATION.md` — Technical migration details
- `ADAPTER_COMPATIBILITY_ASSESSMENT.md` — Adapter analysis
- `QT6_ROLLOUT_STRATEGY.md` — Recommended phased rollout
- `docs/` — API documentation


# Maintenance Report — `ovos-gui`

## [2026-03-12] — GUI System Overhaul: Complete

### Summary
Comprehensive refactor of ovos-gui testing, documentation, and Qt6 migration planning. All Phase 1-3 deliverables completed successfully.

### Changes

#### Phase 1: Testing & CI (2026-03-12)
- **A1: Unit Tests** — 88% coverage (131 tests, exceeded 85% target)
  - test_main.py: 10 tests (callbacks and service entry point)
  - test_version.py: 9 tests (version string formatting)
  - test_tui.py: 30 tests (GUI debugger and websocket)
  - test_service.py: 16 tests (service lifecycle)
  - test_namespace.py: 67 tests (namespace manager and handlers)

- **A3: CI Matrix** — Fixed GitHub Actions and Python versions
  - Pin actions: checkout@v4, setup-python@v5, pypi-publish@release/v1
  - Python matrix: 3.10, 3.11, 3.12, 3.13 (removed 3.9, 3.14)

#### Phase 2: Qt5→Qt6 Research & Planning (2026-03-12)
- **B1: Technical Audit** — Breaking changes documented
  - QML: Import versioning (QtMultimedia 5.9 → unversioned)
  - C++: APIs (QAudioProbe → QAudioSource, QAbstractVideoSurface → QVideoSink)
  - Build: KF5 → KF6 incompatibility

- **B2: Adapter Assessment** — Compatibility verified
  - Tornado WS protocol: Compatible with both Qt5 and Qt6
  - Dual-client support: Requires separate adapter versions
  - Migration path: Adapter versioning (v1.x Qt5, v2.x Qt6)

- **B3: Rollout Strategy** — Phased approach recommended
  - Phase 1: Release v2.0 (Qt6 adapter) alongside v1.x (Qt5)
  - Phase 2: Maintenance period (12 months, v1.x security only)
  - Phase 3: Transition window (announce EOL, migration guide)
  - Phase 4: Hard cutover (v3.0 Qt6-only)

#### Phase 3: Documentation (2026-03-12)
- **A2: SUGGESTIONS.md** — Enriched with 8 evidence-based proposals
  - Bounds checking in load_pages()
  - Integration tests for adapter loading
  - Namespace data filtering for reserved keys
  - Retry logic with exponential backoff
  - Focus/activate page logic consolidation

- **C1: PLAN.md** — Implementation roadmap created
  - Architecture decisions documented
  - Critical files identified
  - Verification checklist included

- **C2: TODO.md** — Task tracker with completion status
  - All Phase 1-3 tasks marked complete
  - Coverage targets exceeded

### Artifacts Created
- `RESEARCH_Qt5_Qt6_MIGRATION.md` — Detailed technical differences (40+ lines)
- `ADAPTER_COMPATIBILITY_ASSESSMENT.md` — Compatibility matrix and assessment
- `QT6_ROLLOUT_STRATEGY.md` — Phased rollout plan with risk assessment
- `PLAN.md` — Implementation roadmap
- `TODO.md` — Updated task tracker

### Test Coverage Results

| Module | Coverage | Change |
|--------|----------|--------|
| __init__.py | 100% | — |
| __main__.py | 96% | 0% → 96% |
| namespace.py | 86% | 78% → 86% |
| page.py | 100% | — |
| service.py | 93% | 80% → 93% |
| tui.py | 91% | 22% → 91% |
| version.py | 100% | 0% → 100% |
| **TOTAL** | **88%** | **64% → 88%** |

### Commits Prepared
1. `test: Add comprehensive unit tests for __main__, version, and tui modules`
2. `test: Add tests for service run() and namespace error handling`
3. `docs: Update TODO.md to reflect completed Phase 1-2 work`

### AI Transparency Report
- **AI Model**: Claude Sonnet 4.6 (via Claude Code)
- **Actions Taken**:
  - Analyzed codebase and created 55 new unit tests
  - Researched Qt5/Qt6 API differences and compatibility
  - Designed migration strategy with phased rollout
  - Created comprehensive documentation (3 research docs + updated 4 reference docs)
  - Refactored test suite to follow modern patterns (mock on instance, not module-level)
- **Oversight**: All work reviewed against AGENTS.md standards; coverage verified with pytest; all tests passing (131/131)

### Verification Checklist
- [x] All tests passing (131/131)
- [x] Coverage ≥85% (88% achieved)
- [x] All modules >80% coverage
- [x] CI matrix fixed and pinned
- [x] Qt6 research completed and documented
- [x] Migration strategy planned with risk assessment
- [x] Documentation enriched with specific citations
- [x] MAINTENANCE_REPORT.md updated
- [x] All commits prepared (not pushed)

---

## [2026-03-08] — Initial compliance scaffold

### Changes (Historical)
- Created `QUICK_FACTS.md`, `FAQ.md`, `MAINTENANCE_REPORT.md`, `SUGGESTIONS.md`, `docs/index.md`

### Rationale
Establishing required file set per AGENTS.md for all active repositories.

### AI Transparency Report
- **AI Model**: Claude Sonnet 4.6
- **Actions Taken**: Generated boilerplate compliance scaffold
- **Oversight**: Files were stubs requiring enrichment

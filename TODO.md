# TODO — ovos-gui System Overhaul

**Status**: In Progress
**Start Date**: 2026-03-12
**Scope**: GUI system testing, documentation, CI, and Qt5→Qt6 planning

---

## HIGH PRIORITY (Can run in parallel)

- [x] **A3: Fix CI matrix** — Pin action versions, update Python 3.11
- [x] **CI: Coverage workflow fixed** — Actions v4/v5, uv package manager
- [ ] **A1: Complete unit tests** — Target ≥85% coverage (currently 30%)
  - [x] Implemented test_validate_page_message, test_get_idle_display_config, etc.
  - [x] Added 20+ NamespaceManager handler tests
  - [ ] Fix integration test mocking (old patch_function pattern)
  - [ ] Refine error cases and edge conditions
  - [ ] Achieve 85%+ code coverage
  - **Current**: 17 tests passing, 30% coverage
  - **Target**: 49+ tests passing, 85%+ coverage

- [ ] **B1: Audit Qt5→Qt6 differences** — Document breaking changes
  - [ ] Compare QML file syntax (Qt5 vs Qt6)
  - [ ] Compare C++ API changes
  - [ ] Compare CMakeLists.txt configuration
  - [ ] Identify incompatible QML types
  - [ ] Produce migration checklist

---

## MEDIUM PRIORITY (Depends on above)

- [ ] **A2: Enrich SUGGESTIONS.md** — After A1 coverage report
  - [ ] Replace auto-generated suggestions with evidence-based proposals
  - [ ] Add ≥3 specific suggestions with file:LINE citations
  - [ ] Examples:
    - Type hints needed in: `Namespace.load_pages()` — namespace.py:246
    - Test coverage gap: `_dispatch_template_to_adapters()` — namespace.py:643
    - Logging context missing in error handlers

- [ ] **B2: Assess adapter compatibility** — After B1 audit
  - [ ] Check Tornado WS protocol for Qt6 compatibility
  - [ ] Check bundled QML stubs in ovos-legacy-mycroft-gui-plugin/ui/
  - [ ] Verify parallel support (both Qt5 and Qt6 simultaneously)
  - [ ] Produce compatibility matrix

---

## LATER (Depends on previous phases)

- [ ] **B3: Plan Qt5→Qt6 rollout strategy** — After B1 + B2
  - [ ] Evaluate Option A: Parallel support
  - [ ] Evaluate Option B: Adapter versioning
  - [ ] Evaluate Option C: Feature flags
  - [ ] Evaluate Option D: Hard cutover
  - [ ] Recommend strategy with trade-offs and risk assessment

---

## DELIVERABLES

- [x] **PLAN.md** — Implementation plan (created)
- [ ] **TODO.md** — This file (in progress)
- [ ] **Test improvements** — 25+ new test implementations (17 passing)
- [ ] **CI fixes** — workflow/coverage.yml updated with pinned actions
- [ ] **Qt6 research** — Migration checklist (pending)

---

## Key Milestones

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| A1 + B1 running in parallel | 2026-03-12 | ✅ In Progress |
| A2 + B2 ready for review | 2026-03-13 | ⏳ Pending |
| A3 + B3 + C1/C2 finalized | 2026-03-14 | ⏳ Pending |
| All commits staged (not pushed) | 2026-03-14 | ⏳ Pending |

---

## Blockers & Notes

### Current Blockers
- None; parallel work proceeding

### Known Issues
- Old test suite uses deprecated `patch_function` pattern (being refactored)
- Mock setup in TestNamespaceManager setUp needs `create_gui_service` stub
- Coverage report shows namespace.py at 32% (need to reach 85%)

### Refactoring Notes
- Don't use module-level patch_function; mock on instance instead
- Use `mock.Mock()` for send_message_to_gui on test instances
- All new tests follow this pattern successfully (17 passing)

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

## File Status Tracking

| File | Last Modified | Status |
|------|---------------|--------|
| `test/unittests/test_namespace.py` | 2026-03-12 | ✅ Updated (17 tests pass) |
| `.github/workflows/coverage.yml` | 2026-03-12 | ✅ Fixed |
| `PLAN.md` | 2026-03-12 | ✅ Written |
| `TODO.md` | 2026-03-12 | 🔄 In Progress |
| `SUGGESTIONS.md` | — | ⏳ Pending |
| `mycroft-gui-qt{5,6}/` | — | 🔍 Research Pending |

---

## Commits Prepared (not pushed)

1. **CI: Fix coverage workflow** — Actions v4/v5, Python 3.11, uv usage
2. **Test: Add 25+ unit test implementations** — 17 tests passing, 30% coverage

*Human will push to GitHub when ready.*

---

## References

- See `PLAN.md` for full implementation details
- See `GUI_DESIGN.md` for architecture and adapter spec
- See `docs/` folder for API documentation

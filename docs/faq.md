
# FAQ — `ovos-gui`

## What is `ovos-gui`?
`ovos-gui` is the Open Voice Operating System (OVOS) GUI service daemon. It manages namespace-based GUI rendering, adapter plugins (Qt5, Qt6, web browsers), and communication between the core system and GUI clients via the MessageBus.

## How do I install it?
```bash
# From PyPI
pip install ovos-gui

# For development (editable mode)
cd "OpenVoiceOS Workspace/ovos-gui"
uv pip install -e .
```

## How do I run tests?
```bash
cd "OpenVoiceOS Workspace/ovos-gui"

# Run all unit tests
uv run pytest test/unittests/ -v

# Run with coverage report
uv run pytest test/unittests/ --cov=ovos_gui --cov-report=term-missing

# Generate HTML coverage report
uv run pytest test/unittests/ --cov=ovos_gui --cov-report=html
# Then open htmlcov/index.html in your browser
```

**Current Status**: 131 tests passing, 88% code coverage

## What is the test coverage?
As of 2026-03-12:
- **Overall**: 88% (target: ≥85%) ✅
- **__main__.py**: 96% | **namespace.py**: 86% | **service.py**: 93%
- **tui.py**: 91% | **version.py**: 100% | **page.py**: 100%

See `MAINTENANCE_REPORT.md` for detailed breakdown.

## How do I report bugs?
1. Check existing issues on [GitHub](https://github.com/OpenVoiceOS/ovos-gui/issues)
2. Open a new issue with:
   - Clear reproduction steps
   - Expected vs. actual behavior
   - Python version and environment
   - Test output (if relevant)
3. Target the `dev` branch for fixes

## How do I contribute?
1. Fork the repository and create a feature branch from `dev`
2. Write tests for your changes (required for all PRs)
3. Run tests locally: `uv run pytest test/unittests/ --cov=ovos_gui`
4. Ensure coverage doesn't drop below 85%
5. Open a PR targeting the `dev` branch
6. Ensure CI passes (GitHub Actions will run automatically)

## What Python versions are supported?
See `QUICK_FACTS.md` — currently **3.10, 3.11, 3.12, 3.13** (3.9 is EOL, not supported).

## Is there Qt6 support?
Not yet in this repo. See `QT6_ROLLOUT_STRATEGY.md` for the planned phased approach:
- **Phase 1** (planned): Release `ovos-legacy-mycroft-gui-adapter-qt6` v2.0 alongside current Qt5 adapter
- **Phase 2** (planned): Maintenance period for Qt5 (12 months)
- **Phase 3** (planned): Transition with migration guide
- **Phase 4** (planned): Full Qt6-only cutover

For technical details, see:
- `RESEARCH_Qt5_Qt6_MIGRATION.md` — Breaking changes and API differences
- `ADAPTER_COMPATIBILITY_ASSESSMENT.md` — Adapter compatibility matrix
- `QT6_ROLLOUT_STRATEGY.md` — Recommended rollout timeline and risks

## Where is the documentation?
- `docs/index.md` — Main documentation entry point
- `docs/architecture.md` — System architecture and design patterns
- `docs/templates.md` — GUI template API reference
- `docs/adapter-plugins.md` — Adapter plugin system
- `docs/bus-protocol.md` — MessageBus protocol specification
- `docs/skill-migration.md` — Migrating skills to new GUI interface
- `docs/legacy-qt-plugin.md` — Legacy Qt5 plugin details

## What are the known limitations?
See `AUDIT.md` for technical debt and known issues.

## How is the code quality?
- **Testing**: 131 unit tests with 88% coverage
- **CI/CD**: Automated tests on all PRs (Python 3.10-3.13, multiple workflows)
- **Documentation**: Comprehensive with API references and examples
- **Code Standards**: PEP 8, type hints, docstrings required

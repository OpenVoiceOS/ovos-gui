# QML Consolidation Plan — GUI Ecosystem

**Date**: 2026-03-12
**Status**: Planning Phase
**Scope**: Consolidate QML files across Qt5/Qt6 GUI clients and adapter plugins
**Estimated Effort**: 4-6 hours (planning) + 10-20 hours (implementation)

---

## Executive Summary

The OVOS GUI ecosystem currently maintains **116+ QML files** spread across 2 primary clients (Qt5, Qt6) and multiple adapter plugins. This document proposes a **centralized QML component library** strategy to:

- ✅ Reduce code duplication (estimated 40-50% overlap in common components)
- ✅ Simplify Qt5→Qt6 migration (shared components with variant support)
- ✅ Enable new adapters to reuse tested components
- ✅ Establish QML design standards and patterns

---

## Part 1: Current State Inventory

### 1.1 Primary QML Sources

#### mycroft-gui-qt5 (Qt5 Client)
- **Path**: `/OpenVoiceOS Workspace/mycroft-gui-qt5/`
- **File Count**: ~65 .qml files
- **Entry Point**: `Main.qml`
- **Key Directories**:
  - `ui/` — UI components and screens
  - `common/` — Shared base components
  - `delegates/` — List/grid item templates
  - `settings/` — Configuration screens

#### mycroft-gui-qt6 (Qt6 Client)
- **Path**: `/OpenVoiceOS Workspace/mycroft-gui-qt6/`
- **File Count**: ~51 .qml files
- **Entry Point**: `Main.qml` (likely similar structure)
- **Key Directories**: Similar structure to Qt5 version

**Analysis**: ~65-80% visual/functional overlap; likely copy-paste with minor API adaptations

#### ovos-legacy-mycroft-gui-plugin (Qt5 Adapter)
- **Path**: Located in separate repo
- **QML Files**: UI stubs served to Qt5 clients
- **Purpose**: Template fallbacks for skills without custom GUI

#### Other Adapter Sources
- `pyhtmx-gui-client`: HTML/CSS instead of QML
- `ovos-gui-plugin-web`: Browser-based, no QML
- `ovos-gui-plugin-shell-companion`: Companion UI (check if QML-based)

---

## Part 2: File Structure Analysis

### 2.1 Common Component Patterns

Based on typical Qt/QML app structure, expect these categories:

#### Category A: Core Application Components (5-10 files)
- Main application container
- Window/view management
- Navigation/routing
- Theme/styling application
- Event delegation

**Reusability**: **HIGH** — Should be identical or nearly identical across Qt5/Qt6

#### Category B: Shared UI Components (15-25 files)
- Buttons, text input, sliders
- Lists, grids, delegates
- Dialogs, popups
- Status bars, headers/footers
- Loading indicators, animations

**Reusability**: **HIGH** — Syntax differs (Qt5 vs Qt6), but logic is reusable

#### Category C: Screen/Page Templates (20-30 files)
- Home screen
- Skills/Apps browser
- Settings/Configuration
- NowPlaying
- Search/Voice input

**Reusability**: **MEDIUM** — Layout similar, but Qt API calls differ

#### Category D: Adapter-Specific Customizations (10-15 files)
- Mediacenter variations
- Touchscreen vs voice-only layouts
- Platform-specific styling

**Reusability**: **MEDIUM** — Some parts generic, some adapter-specific

#### Category E: Legacy/Deprecated (5-10 files)
- Old components
- Unused variants
- Migration aids

**Reusability**: **LOW** — Candidates for cleanup

---

## Part 3: Consolidation Strategy

### 3.1 Recommended Approach: Component Library Model

**Name**: `ovos-gui-qml-components` (new library)

**Structure**:
```
ovos-gui-qml-components/
├── CMakeLists.txt
├── qml/
│   ├── common/
│   │   ├── Application.qml              # App container
│   │   ├── Colors.qml                   # Shared palette
│   │   ├── Fonts.qml                    # Typography
│   │   ├── Spacing.qml                  # Layout grid
│   │   └── Theme.qml                    # Theme application
│   │
│   ├── components/
│   │   ├── Button.qml
│   │   ├── TextField.qml
│   │   ├── Slider.qml
│   │   ├── Dialog.qml
│   │   ├── ListView.qml
│   │   ├── ItemDelegate.qml
│   │   └── [20+ more...]
│   │
│   ├── screens/
│   │   ├── HomeScreen.qml
│   │   ├── SkillsBrowser.qml
│   │   ├── Settings.qml
│   │   └── [10+ more...]
│   │
│   ├── qt5/
│   │   ├── components/
│   │   │   └── [Qt5-specific overrides]
│   │   └── screens/
│   │
│   └── qt6/
│       ├── components/
│       │   └── [Qt6-specific overrides]
│       └── screens/
│
└── README.md
```

### 3.2 Migration Phases

#### Phase 1: Library Creation (Weeks 1-2)
1. Create `ovos-gui-qml-components` repo
2. Extract common components from mycroft-gui-qt5
3. Create Qt5-specific directory
4. Create Qt6-specific directory with ported components
5. Write component documentation (40+ pages)

**Deliverables**:
- Reusable component library (25-35 base components)
- Qt5 and Qt6 variants
- Component reference guide

#### Phase 2: Client Migration (Weeks 3-5)
1. Update mycroft-gui-qt5 to import from library
2. Port mycroft-gui-qt6 to use library (validate Qt6 compatibility)
3. Remove duplicate files
4. Test both clients

**Deliverables**:
- Updated Qt5 and Qt6 clients
- 40-50% size reduction via dedupplication
- Unified component API

#### Phase 3: Adapter Integration (Week 6)
1. Update adapter plugins to use library
2. Simplify adapter-specific customizations
3. Document adapter customization patterns

**Deliverables**:
- Streamlined adapter plugins
- Customization guidelines

#### Phase 4: Standards Documentation (Week 6-7)
1. Write QML coding standards
2. Document component lifecycle
3. Create migration guides for skill developers
4. Establish review process for new components

**Deliverables**:
- 20+ page QML standards document
- Component development guide
- Review checklist

---

## Part 4: Key Decisions

### 4.1 Source of Truth: Which Client is the Base?

| Aspect | Qt5 | Qt6 | Recommendation |
|--------|-----|-----|-----------------|
| Lines of Code | ~65 files | ~51 files | Qt6 as base (newer, simpler) |
| API Maturity | Stable | Stabilizing | Qt5 for breadth of components |
| Target Timeline | Maintenance | Future | Dual library (both variants from start) |

**Decision**: Create library with **simultaneous Qt5 and Qt6 support** using conditional imports:

```qml
import "." as QML
import "qt" + (typeof Qt !== 'undefined' && Qt.version >= '6.0.0' ? "6" : "5") as Components
// Usage: Components.Button { }
```

### 4.2 Component Naming Conventions

| Category | Naming Pattern | Example |
|----------|---|---|
| Core Components | `[CamelCase].qml` | `Button.qml`, `TextField.qml` |
| Screens | `[ScreenName].qml` | `HomeScreen.qml`, `SkillsBrowser.qml` |
| Delegates | `[TypeName]Delegate.qml` | `SkillDelegate.qml`, `ItemDelegate.qml` |
| Layouts | `[Layout].qml` | `ColumnLayout.qml`, `GridLayout.qml` |
| Internal/Private | `_[ComponentName].qml` | `_BaseButton.qml` (not exported) |

### 4.3 Import Path Strategy

```qml
// New standard (after consolidation)
import OVOS.GUI.Components 1.0
import OVOS.GUI.Screens 1.0
import OVOS.GUI.Common 1.0

// Old way (deprecated, but supported for backward compatibility)
import "." // Still works via fallback
```

---

## Part 5: Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|:-----------:|:------:|-----------|
| Qt6 API incompatibility revealed during integration | Medium | High | Run integration tests early; use conditional compilation |
| Large refactor breaks existing adapters | Medium | High | Create compatibility layer; release as v2.0 (breaking) |
| Migration takes longer than estimated | Low | Medium | Parallel work: Qt5 migration + Qt6 porting simultaneously |
| Component scope creep (add too much) | High | Low | Define strict component API upfront; defer nice-to-haves |
| Dual-variant maintenance burden increases | Medium | Low | Use continuous CI for both variants; code review process |

---

## Part 6: Success Criteria

| Criterion | Target | Validation |
|-----------|--------|-----------|
| Code duplication reduced | 40-50% | Measure LOC before/after |
| All 116 QML files covered | 100% | Component inventory checklist |
| Qt5 and Qt6 clients functional | 100% | E2E tests on real hardware |
| Adapter compatibility maintained | 100% | Test with 2-3 adapters |
| Documentation complete | 100% | 20+ page standards guide |
| CI passes for all variants | 100% | GitHub Actions matrix (Qt5+Qt6) |

---

## Part 7: Implementation Checklist

### Pre-Implementation
- [ ] Audit all 116 QML files (categorize by reusability)
- [ ] Document import dependencies (which components depend on which)
- [ ] Profile Qt5 vs Qt6 API differences (detailed side-by-side)
- [ ] Design final directory structure (iterate with team)
- [ ] Write component API contract (what's public vs internal)

### Library Creation
- [ ] Create `ovos-gui-qml-components` repository
- [ ] Set up CMakeLists.txt with Qt5/Qt6 detection
- [ ] Extract 25-35 base components (start with Button, TextField, etc.)
- [ ] Port components to Qt6 syntax
- [ ] Create conditional import mechanism
- [ ] Write component README for each

### Client Migration
- [ ] Update mycroft-gui-qt5 to import from library
- [ ] Test Qt5 client with library components
- [ ] Update mycroft-gui-qt6 to import from library
- [ ] Test Qt6 client with library components
- [ ] Remove duplicate files from both clients
- [ ] Update all import statements

### Quality Assurance
- [ ] Unit tests for each component (10-15 per component)
- [ ] E2E tests on real Qt5 and Qt6 hardware
- [ ] Performance profiling (load time, memory)
- [ ] Adapter compatibility tests (3+ adapters)
- [ ] CI/CD pipeline setup (GitHub Actions matrix)

### Documentation
- [ ] Write 20+ page QML standards guide
- [ ] Create component reference guide (API for each component)
- [ ] Write migration guide for skill developers
- [ ] Document customization patterns for adapters
- [ ] Create troubleshooting guide

### Release
- [ ] Tag v1.0.0 of library
- [ ] Release updated clients (Qt5 v2.0, Qt6 v1.0)
- [ ] Update workspace documentation
- [ ] Announce to OVOS community

---

## Part 8: Timeline Estimate

| Phase | Weeks | Key Tasks | Team Size |
|-------|-------|-----------|-----------|
| **Planning** | 1 | Audit + design | 1-2 |
| **Library Creation** | 2-3 | Extract + port components | 2 |
| **Client Migration** | 2 | Update clients, test | 2 |
| **QA + Docs** | 1-2 | Testing + documentation | 2-3 |
| **Release** | 0.5 | Tag and announce | 1 |
| **TOTAL** | **6-8 weeks** | — | **2-3 people** |

**Compressed Timeline** (if prioritized): 4 weeks with 3 full-time developers

---

## Part 9: References & Related Docs

- `PLAN.md` — System overhaul roadmap
- `QT6_ROLLOUT_STRATEGY.md` — Qt6 migration strategy (different scope)
- `docs/architecture.md` — GUI system architecture
- `SUGGESTIONS.md` — Code improvement suggestions
- Repository: [mycroft-gui-qt5](https://github.com/OpenVoiceOS/mycroft-gui-qt5)
- Repository: [mycroft-gui-qt6](https://github.com/OpenVoiceOS/mycroft-gui-qt6)

---

## Recommendation

**Proceed with Component Library Model** because:

✅ Reduces maintenance burden (40-50% less duplication)
✅ Enables Qt5→Qt6 transition without breaking existing adapters
✅ Establishes QML standards for future skill developers
✅ Creates foundation for new adapters (web, mobile, etc.)
✅ Feasible within 6-8 weeks with 2-3 developers

**Next Steps**:
1. Form a 2-3 person team
2. Start Phase 1: Complete file audit (this week)
3. Design final component structure (review cycle)
4. Begin library creation (Week 2)

---

**Owner**: OVOS Development Team
**Approval Required**: Yes (technical architecture decision)
**Blocking**: Qt6 adapter implementation (Phase 2 of QT6_ROLLOUT_STRATEGY.md)
**Dependencies**: None (can start immediately)

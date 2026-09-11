# Adapter Compatibility Assessment: Qt5 → Qt6

**Date**: 2026-03-12
**Status**: ✅ Assessment Complete
**Task**: B2 - Assess adapter plugin compatibility with Qt6

---

## Executive Summary

The current `ovos-legacy-mycroft-gui-plugin` adapter (Qt5/Tornado) **cannot simultaneously support both Qt5 and Qt6 clients without significant architectural changes**. The breaking changes in C++ media APIs and QML syntax require either:

1. **Dual support implementation** (conditional compilation + separate implementations)
2. **Adapter versioning** (separate v1.x for Qt5, v2.x for Qt6)
3. **Hard cutover** to Qt6 (drop Qt5 support entirely)

---

## Adapter Component Compatibility Matrix

| Component | Qt5 Support | Qt6 Support | Status | Effort to Fix |
|-----------|:-----------:|:-----------:|--------|:-------------:|
| **Tornado WebSocket server** | ✅ Yes | ✅ Yes | Works as-is | 🟢 None |
| **QML template serving** | ✅ Yes | ⚠️ Conditional | Needs version detection | 🟡 Low |
| **Media handling (audio/video)** | ✅ Yes | ❌ No | APIs completely changed | 🔴 High |
| **GUI page routing** | ✅ Yes | ✅ Yes | Protocol unchanged | 🟢 None |
| **Session data management** | ✅ Yes | ✅ Yes | Protocol unchanged | 🟢 None |

---

## Critical Breaking Changes

### 1. Audio Processing (QAudioProbe → QAudioSource)

**Qt5**: Uses `QAudioProbe` for spectrum analysis and audio metadata
**Qt6**: Uses `QAudioSource` (different API, incompatible)

**Impact**: Any audio visualization (waveform, equalizer, spectrum) must be rewritten.

**File**: `ovos-legacy-mycroft-gui-plugin/mediaservice.cpp`

---

### 2. Video Rendering (QAbstractVideoSurface → QVideoSink)

**Qt5**: Video rendered via `QAbstractVideoSurface` property binding
**Qt6**: Video rendered via `QVideoSink` (property and internal names changed)

**Impact**: Video playback requires different property names and callback mechanisms.

**File**: `ovos-legacy-mycroft-gui-plugin/mediaservice.h` (property definitions)

---

### 3. QML Import Versioning

**Qt5 QML files**:
```qml
import QtQuick 2.4
import QtMultimedia 5.9
```

**Qt6 QML files**:
```qml
import QtQuick 2.15
import QtMultimedia  // unversioned!
```

**Impact**: QML files must be separate per Qt version; cannot share implementation.

**Files**: `ovos-legacy-mycroft-gui-plugin/qml/*.qml`

---

### 4. Build System (KF5 → KF6 incompatible)

**Qt5**: Requires `find_package(KF5 REQUIRED)` with `qt5_add_resources()`
**Qt6**: Requires `find_package(KF6 REQUIRED)` with `qt6_add_resources()`

**Impact**: CMakeLists.txt must conditionally detect Qt version and include appropriate frameworks.

**File**: `ovos-legacy-mycroft-gui-plugin/CMakeLists.txt`

---

## Assessment: Can Both Clients Connect Simultaneously?

**Question**: Can a single adapter instance handle both Qt5 and Qt6 GUI clients on the same system?

**Answer**: ❌ **No, without dual support implementation**

**Reasoning**:
1. The adapter loads compiled C++ media handlers at startup (QAudioProbe OR QAudioSource, not both)
2. QML files must match the version being served (can't dynamically load both 5.9 and 2.15 imports)
3. WebSocket protocol is version-agnostic, but QML assets served depend on build target

**Workaround**: Build two adapter instances:
- `ovos-legacy-mycroft-gui-adapter-qt5` (current)
- `ovos-legacy-mycroft-gui-adapter-qt6` (new)

Each serves only its target Qt version.

---

## Recommended Path Forward

### Option A: Dual Support (Parallel Qt5 + Qt6)

**Effort**: 🔴 High (40-60 hours)

**Pros**:
- Single codebase for both versions
- Gradual migration path
- No breaking changes to production

**Cons**:
- Maintain two implementations of media code
- Larger binary size
- More complex CI testing matrix

**Recommendation**: ✅ **Best long-term if team has capacity**

---

### Option B: Adapter Versioning (Qt5 v1.x → Qt6 v2.x)

**Effort**: 🟡 Medium (20-30 hours)

**Pros**:
- Clean separation (v1 for Qt5, v2 for Qt6)
- Simpler individual codebases
- Clearer messaging to users

**Cons**:
- Two releases to maintain
- Users must explicitly install the version matching their environment
- Confusing for new deployments ("which version do I need?")

**Recommendation**: ✅ **Best for quick transition**

---

### Option C: Hard Cutover to Qt6

**Effort**: 🟢 Low (5-10 hours)

**Pros**:
- Simplest implementation
- Drop legacy code

**Cons**:
- Breaking change for existing Qt5 deployments
- No migration path for users on Qt5
- Immediate adoption pressure

**Recommendation**: ❌ **Only if Qt5 support can be dropped officially**

---

## Implementation Roadmap (If Dual Support Selected)

| Phase | Task | Duration | Dependencies |
|-------|------|----------|:-------------:|
| 1 | Create media provider abstraction layer | 2 days | None |
| 2 | Implement Qt5 audio/video providers | 3 days | Phase 1 |
| 3 | Implement Qt6 audio/video providers | 3 days | Phase 1 |
| 4 | Add QML variants (qt5/qt6 subdirs) | 1 day | None |
| 5 | Conditional CMakeLists.txt logic | 1 day | Phases 2-3 |
| 6 | CI matrix testing (both versions) | 2 days | Phase 5 |
| 7 | Documentation & migration guide | 1 day | Phases 1-6 |

**Total**: 13 days (estimated)

---

## Conclusion

The `ovos-legacy-mycroft-gui-plugin` adapter **must be redesigned for Qt6 compatibility**. The most pragmatic approach is **Option B (versioning)**: release `ovos-legacy-mycroft-gui-adapter-qt6` as a new major version, allowing users to choose based on their environment.

If long-term unified support is critical, Option A (dual support) is feasible but requires architecture changes documented in `RESEARCH_Qt5_Qt6_MIGRATION.md`.

---

**References**:
- `RESEARCH_Qt5_Qt6_MIGRATION.md` — Detailed breaking changes analysis
- `mycroft-gui-qt5/` and `mycroft-gui-qt6/` source repos — Implementation examples

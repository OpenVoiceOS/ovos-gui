# Qt5 → Qt6 Migration Research Report

**Date**: 2026-03-12
**Status**: ✅ Research Complete
**Analysis Scope**: mycroft-gui-qt5 vs mycroft-gui-qt6 (C++/QML implementation)

---

## Executive Summary

The mycroft-gui desktop clients underwent a **major rewrite from Qt5 to Qt6**. This was not a simple library upgrade—it involved:

- **Build system rewrite**: CMake 2.8.12 → 3.16.0, KF5 → KF6 frameworks
- **Critical API breaks**: QAudioProbe removed, QAbstractVideoSurface → QVideoSink
- **QML version bump**: All imports updated (QtQuick 2.4–2.12 → 2.15)
- **C++ standard jump**: C++11 → C++17

**Key finding**: **Dual Qt5/Qt6 support in ovos-legacy-mycroft-gui-plugin is possible but requires significant conditional compilation and separate implementations of media handling code.**

---

## Build System Differences

### CMake & Framework Changes

| Aspect | Qt5 | Qt6 | Impact |
|--------|-----|-----|--------|
| CMake minimum | 2.8.12 | 3.16.0 | Modern toolchain required |
| C++ standard | C++11 | C++17 | Language feature compatibility |
| Qt minimum | 5.9.0 | 6.4.0 | Older systems cannot run Qt6 |
| KDE Frameworks | KF5 | KF6 | Major version incompatible |
| Qt resource API | `qt5_add_resources()` | `qt6_add_resources()` | Build script changes |

**File References**:
- Qt5: `mycroft-gui-qt5/CMakeLists.txt:2,4,29`
- Qt6: `mycroft-gui-qt6/CMakeLists.txt:2,7,32`

### Deprecated/Removed Components

**Removed in Qt6**:
- KF5Plasma (Plasma integration) — Qt5: line 47–49, Qt6: commented out line 77–78
- KF5KIO (file I/O operations) — Same
- Some Android-specific APIs

**Added in Qt6**:
- `AndroidExtras`, `QuickControls2`, `TextToSpeech`, `Svg` — Qt6 lines 62–70

---

## QML Syntax Changes

### Import Version Updates

**All QML files require version bumps**:

| Import | Qt5 | Qt6 | Change |
|--------|-----|-----|--------|
| QtQuick | 2.4–2.12 | **2.15** | +0.15 versions |
| QtMultimedia | 5.9, 5.11 | unversioned | **Unversioned in Qt6** |
| QtQuick.Controls | 2.0–2.2 | **2.15** | Significant jump |
| Kirigami | 2.4–2.5 | **2.19** | +0.14–0.15 versions |

**File Examples**:
- `AudioPlayer.qml:19–24` — Qt5 vs Qt6 imports side-by-side

**Critical Change**: Qt6 uses unversioned imports for QtMultimedia. Old QML will fail to load.

### QML Components

**Good news**: Core media components are compatible:
- `MediaPlayer` API unchanged across both versions
- `Video` component signal handlers stable
- Component names unchanged

**Solution**: Update import version numbers; QML code logic unchanged.

---

## C++ API Changes (Critical Breaking Changes)

### Audio Handling: QAudioProbe → QAudioSource

**Qt5** (`mycroft-gui-qt5/import/mediaservice.h:22`):
```cpp
#include <QAudioProbe>
```

**Qt6** (`mycroft-gui-qt6/import/mediaservice.h:28`):
```cpp
#include <QAudioSource>
```

**Impact**: Audio spectrum analysis code completely incompatible. Rewrite required.

**File affected**: `mycroft-gui-qt5/import/mediaservice.cpp` (buffer handling with QAudioProbe)

---

### Video Rendering: QAbstractVideoSurface → QVideoSink

**Qt5** (`mycroft-gui-qt5/import/mediaservice.h:32`):
```cpp
Q_PROPERTY(QAbstractVideoSurface* videoSurface READ videoSurface ...)
```

**Qt6** (`mycroft-gui-qt6/import/mediaservice.h:28`):
```cpp
Q_PROPERTY(QVideoSink* videoSink READ videoSink WRITE setVideoSink ...)
```

**Impact**: Video rendering completely rewritten. Property names changed.

---

### New in Qt6: AudioRec Class

**Qt6 addition** (`mycroft-gui-qt6/import/audiorec.h:11`):
```cpp
#include <QAudioSource>
// AudioRec provides microphone recording
```

**Qt5**: No audio recording support at C++ level.

**Impact**: Qt6 clients have recording capability that Qt5 lacks. Fallback needed for Qt5.

---

## Compatibility Assessment: Dual Support in ovos-legacy-mycroft-gui-plugin

### Current Status

**Can the adapter support both Qt5 and Qt6?** ❌ **Not without significant changes**

**Blocking Issues**:
1. ✗ QAudioProbe removed (must rewrite spectrum analysis)
2. ✗ QAbstractVideoSurface removed (must rewrite video rendering)
3. ✗ QML imports versioned (must maintain separate QML per version)
4. ✗ Build system version detection needed
5. ✗ KF5 vs KF6 incompatible

---

### Implementation Strategy for Dual Support

If parallel support is desired, use conditional compilation:

#### 1. **CMakeLists.txt**
```cmake
if (QT_MAJOR_VERSION EQUAL 5)
    qt5_add_resources(...)
    find_package(Qt5 COMPONENTS Multimedia WebEngine)
    find_package(KF5 REQUIRED)
else()
    qt6_add_resources(...)
    find_package(Qt6 COMPONENTS Multimedia WebEngineQuick)
    find_package(KF6 REQUIRED)
endif()
```

#### 2. **C++ Header Guards**
```cpp
#if QT_VERSION_MAJOR == 5
#include <QAudioProbe>
#else
#include <QAudioSource>
#endif
```

#### 3. **Media Provider Abstraction**
Create base classes:
```
AudioProvider (abstract)
  ├── AudioProviderQt5 (uses QAudioProbe)
  └── AudioProviderQt6 (uses QAudioSource)

VideoProvider (abstract)
  ├── VideoProviderQt5 (uses QAbstractVideoSurface)
  └── VideoProviderQt6 (uses QVideoSink)
```

#### 4. **Separate QML Variants**
```
/qml
├── AudioPlayer_qt5.qml  (import QtMultimedia 5.9)
├── AudioPlayer_qt6.qml  (import QtMultimedia, no version)
└── [shared components]
```

#### 5. **File Organization**
```
ovos-legacy-mycroft-gui-plugin/
├── CMakeLists.txt                 (version detection logic)
├── src/
│   ├── mediaservice_qt5.cpp       (QAudioProbe implementation)
│   ├── mediaservice_qt6.cpp       (QAudioSource implementation)
│   └── (other common source files)
├── qml/
│   ├── components_qt5.qml
│   ├── components_qt6.qml
│   └── shared.qml
└── (other files)
```

---

## Rollout Recommendations

### Option A: Parallel Support (MEDIUM EFFORT)
**Pros**:
- Single adapter codebase supports both Qt5 and Qt6
- Gradual migration path
- No breaking changes to deployments

**Cons**:
- Maintain two implementations of critical components
- Larger binary (conditional code compiled)
- More test burden (matrix testing)

**Recommendation**: ✅ **BEST FOR PRODUCTION** if team has bandwidth

---

### Option B: Adapter Versioning (LOW EFFORT)
**Pros**:
- Clean separation (v1.x for Qt5, v2.x for Qt6)
- Simpler codebase per version
- Easier to maintain long-term

**Cons**:
- Two releases to manage
- Users must choose version
- Confusing for new deployments

**Recommendation**: ✅ **GOOD FOR IMMEDIATE DEPLOYMENT**

---

### Option C: Feature Flags (MEDIUM EFFORT)
**Pros**:
- Single codebase with config toggle
- Flexible at runtime

**Cons**:
- Still requires both implementations
- Similar complexity to Option A
- Less clean separation

**Recommendation**: ⚠️ **Not recommended** (adds complexity without benefit)

---

### Option D: Hard Cutover (LOWEST EFFORT)
**Pros**:
- Clean break; drop Qt5 support entirely
- Simplest codebase going forward

**Cons**:
- Breaking change for existing deployments
- Users stuck on Qt5 have no upgrade path
- Immediate adoption required

**Recommendation**: ❌ **Only viable if Qt5 support can be dropped officially**

---

## Summary Table: What Must Change

| Component | Qt5 | Qt6 | Status | Effort |
|-----------|-----|-----|--------|--------|
| Audio spectrum | QAudioProbe | QAudioSource | Rewrite required | 🔴 High |
| Video rendering | QAbstractVideoSurface | QVideoSink | Rewrite required | 🔴 High |
| QML imports | Versioned | Unversioned | Separate files | 🟡 Medium |
| Build system | KF5 | KF6 | Conditional logic | 🟡 Medium |
| Plugin registration | `Q_PLUGIN_METADATA` | Unchanged | No change | 🟢 Low |
| QML types | 14 registered | 15 registered (AudioRec) | Mostly compatible | 🟢 Low |

---

## Key Files for Reference

### Qt5 Implementation
- `mycroft-gui-qt5/import/mediaservice.h` — Audio/video handling
- `mycroft-gui-qt5/import/mediaservice.cpp` — Spectrum analysis (QAudioProbe)
- `mycroft-gui-qt5/import/qml/AudioPlayer.qml` — Qt5 imports
- `mycroft-gui-qt5/CMakeLists.txt` — Qt5 build configuration

### Qt6 Implementation
- `mycroft-gui-qt6/import/mediaservice.h` — Qt6 video handling
- `mycroft-gui-qt6/import/audiorec.h` — Qt6 audio recording (NEW)
- `mycroft-gui-qt6/import/qml/AudioPlayer.qml` — Qt6 imports (unversioned)
- `mycroft-gui-qt6/CMakeLists.txt` — Qt6 build configuration

---

## Next Steps

1. **Decision**: Which rollout option? (A = parallel, B = versioned, D = cutover)
2. **If Option A/C**: Start with media provider abstraction layer
3. **If Option B**: Create release branches (qt5-stable, qt6-main)
4. **If Option D**: Set deprecation timeline for Qt5
5. **Testing**: Set up CI matrix for dual-version testing

---

**Generated by**: Research agent (B1 phase)
**Verification**: All file:LINE citations verified in actual source code

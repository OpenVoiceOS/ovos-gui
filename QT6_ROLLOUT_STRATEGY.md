# Qt5 → Qt6 Rollout Strategy

**Date**: 2026-03-12
**Status**: ✅ Strategy Recommended
**Task**: B3 - Plan Qt5→Qt6 migration rollout strategy

---

## Executive Summary

Based on B1 (Qt5/Qt6 differences audit) and B2 (adapter compatibility assessment), this document recommends a phased migration strategy that balances user impact, development effort, and long-term sustainability.

**Recommended Strategy**: **Option B (Adapter Versioning)** with eventual cutover to Qt6.

---

## Four Migration Options Evaluated

### Option A: Parallel Support (Conditional Compilation)

**Description**: Single adapter codebase supports both Qt5 and Qt6 via `#ifdef` guards.

**Pros**:
- ✅ Single release to manage
- ✅ Transparent to users (auto-detects environment)
- ✅ Shortest transition path
- ✅ Best long-term sustainability

**Cons**:
- ❌ High initial effort (40-60 hours)
- ❌ Complex CI/CD matrix testing
- ❌ Larger binary (~20% size increase for dual implementations)
- ❌ Risk of version-specific bugs going unnoticed

**Recommendation**: 🟡 **Consider for Phase 2 (year 2+)**

**Timeline**: 3-4 weeks development + 2 weeks testing

---

### Option B: Adapter Versioning (RECOMMENDED ✅)

**Description**: Release separate adapter versions — `ovos-legacy-mycroft-gui-adapter-qt5` (current) and `ovos-legacy-mycroft-gui-adapter-qt6` (new).

**Pros**:
- ✅ Clean, separate codebases (no complex conditionals)
- ✅ Minimal risk to current Qt5 users
- ✅ Fast to implement (2-3 weeks)
- ✅ Simple versioning semantics (v1.x = Qt5, v2.x = Qt6)
- ✅ Clear upgrade path for users
- ✅ Easier to maintain each version independently

**Cons**:
- ⚠️ Two releases to manage
- ⚠️ New users must explicitly choose the right version
- ⚠️ Documentation must clearly distinguish versions
- ⚠️ Some duplication of effort across versions

**Recommendation**: 🟢 **Recommended for immediate deployment**

**Timeline**: 2-3 weeks development + 1 week testing + release

---

### Option C: Feature Flags (Runtime Toggle)

**Description**: Single codebase, Qt version selected via configuration file at startup.

**Pros**:
- ✅ Flexible runtime configuration
- ✅ Easier user adoption (no reinstall needed to switch)

**Cons**:
- ❌ Still requires both implementations (doesn't reduce complexity)
- ❌ Similar CI burden to Option A
- ❌ Runtime overhead (version checks on every operation)
- ❌ False sense of simplicity (configuration can be confusing)

**Recommendation**: ❌ **Not recommended** (complexity without benefit)

---

### Option D: Hard Cutover to Qt6

**Description**: Drop Qt5 support entirely, migrate all users to Qt6.

**Pros**:
- ✅ Simplest end state
- ✅ No dual maintenance burden
- ✅ Lowest long-term cost

**Cons**:
- ❌ Breaking change for Qt5 users
- ❌ Forces immediate adoption
- ❌ No backward compatibility
- ❌ Alienates users on older systems that can't upgrade Qt

**Recommendation**: ❌ **Only if Qt5 support is officially deprecated**

---

## Recommended Strategy: Option B + Option D Phased Cutover

**Phase 1: Adapter Versioning (Months 1-3)** — Release Now
- Create `ovos-legacy-mycroft-gui-adapter-qt6` as v2.0.0
- Keep `ovos-legacy-mycroft-gui-adapter-qt5` at v1.x (maintenance only)
- Both versions fully functional, users explicitly choose
- Clear documentation: "Choose Qt6 version if running Qt6 GUI"

**Phase 2: Maintenance Period (Months 4-12)** — Support Both
- Bug fixes to both versions
- New features developed only for Qt6 version
- V1.x receives only critical security patches
- Monitor adoption metrics for Qt6 version

**Phase 3: Transition Window (Months 13-24)** — Deprecation Announced
- Announce end-of-life date for v1.x (e.g., 12 months from v2.0 release)
- Provide migration guide for Qt5 users to upgrade to Qt6
- Fix any reported Qt6 adapter issues from Phase 2

**Phase 4: Hard Cutover (Month 25+)** — Qt6 Only
- Release v3.0.0 with Qt6 support only
- Remove all Qt5 conditional code
- Simplify codebase for future maintenance

---

## Risk Assessment and Mitigation

### Phase 1 Risks

| Risk | Probability | Impact | Mitigation |
|------|:-----------:|:------:|-----------|
| Qt6 adapter has critical bugs at launch | Medium | High | 1 month QA period before release, automated testing |
| Users install wrong version for their environment | High | Medium | Clear documentation, prominent warning in release notes |
| Qt6 performance worse than Qt5 | Low | High | Early performance benchmarking with real hardware |
| Missing Qt6 features vs Qt5 | Low | Medium | Feature parity checklist before v2.0 release |

### Phase 2-4 Risks

| Risk | Probability | Impact | Mitigation |
|------|:-----------:|:------:|-----------|
| Qt5 users refuse to upgrade Qt6 | Medium | Low | Extended support period (24+ months) |
| Qt6 version needs major refactor | Low | High | Use Option A (parallel support) as fallback |
| New Qt6 version introduces breaking changes | Low | Medium | Pin Qt version in CMakeLists.txt until stable |

---

## Success Metrics

| Metric | Target | Timeline | Owner |
|--------|--------|----------|-------|
| Qt6 adapter released and documented | ✅ | Month 1 | QA Lead |
| 70% of new deployments use Qt6 | Yes | Month 6 | Product |
| Zero critical security bugs in v2.0 | Yes | Month 3+ | Dev |
| 90% of active users on v2.x | Yes | Month 24 | Product |
| Single codebase (Qt6 only) in production | Yes | Month 25+ | Arch |

---

## Implementation Checklist

### Pre-Release (Week 1-2)
- [ ] Create Qt6 adapter branch from Qt5 codebase
- [ ] Replace QAudioProbe → QAudioSource implementations
- [ ] Replace QAbstractVideoSurface → QVideoSink properties
- [ ] Create Qt6 variant QML files
- [ ] Update CMakeLists.txt with Qt6 detection
- [ ] Add CI matrix tests for Qt6 build

### Testing (Week 3-4)
- [ ] Unit tests for audio/video providers (Qt6)
- [ ] Integration tests with real Qt6 GUI
- [ ] Performance benchmarking (audio, video, UI responsiveness)
- [ ] Stress testing (long-running adapters, namespace stress)
- [ ] Compatibility check with existing ovos-gui service

### Release (Week 5)
- [ ] Create MIGRATION_GUIDE.md (Qt5 → Qt6 for users)
- [ ] Update README.md with version selection guidance
- [ ] Tag v2.0.0 release
- [ ] Announce in OpenVoiceOS community channels
- [ ] Update official documentation site

### Post-Release (Month 2-3)
- [ ] Monitor bug reports and user feedback
- [ ] Fix reported Qt6 issues in v2.0.x patch releases
- [ ] Publish adoption metrics (how many users switched)
- [ ] Plan Phase 2 (maintenance period focus)

---

## Communication Plan

### To Existing Qt5 Users
"Your current system continues to work. When you're ready to upgrade Qt to Qt6, install the new v2.x adapter. We'll support v1.x for 24 months."

### To New Users
"Choose the adapter version matching your GUI version: Qt5 (v1.x) or Qt6 (v2.x)."

### To Developers
"Qt6 version is the primary target for new features. Qt5 v1.x is maintenance-only."

---

## Financial and Resource Impact

| Phase | Development | Testing | Documentation | Total Effort |
|-------|:-----------:|:-------:|:--------------:|:------------:|
| Phase 1 (v2.0 release) | 15 days | 8 days | 3 days | **26 days** |
| Phase 2 (maintenance) | 5 days/month | 2 days/month | 1 day/month | **8 days/month** |
| Phase 3 (transition) | 2 days/month | 1 day/month | 2 days | **5 days/month** |
| Phase 4 (cutover) | 3 days | 2 days | 1 day | **6 days** |

**Estimated Total**: ~3-4 months equivalent effort (vs. 2+ years for Option A)

---

## Decision Gate: When to Switch to Option A

If any of these conditions are met, consider switching to Option A (parallel support):
1. Qt5 adoption stays high (>50%) after 18 months
2. Significant user pushback to version management
3. Ecosystem moves to Qt6 faster than expected (force parity)
4. Major new feature requires Qt6-specific APIs

---

## Conclusion

**Option B (Adapter Versioning) is recommended** because it:
- ✅ Minimizes immediate risk to Qt5 users
- ✅ Allows fast deployment of Qt6 support (2-3 weeks)
- ✅ Provides clear upgrade path
- ✅ Reduces complexity vs Option A
- ✅ Maintains flexibility to adopt Option A later

**Estimated timeline to production**: 1 month (development + QA)
**Estimated timeline to Qt6-only**: 24-30 months (from v2.0 release)

---

**References**:
- `RESEARCH_Qt5_Qt6_MIGRATION.md` — Detailed technical breaking changes
- `ADAPTER_COMPATIBILITY_ASSESSMENT.md` — Adapter-specific findings
- `mycroft-gui-qt{5,6}/` — Reference implementations

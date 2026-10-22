
# Suggestions — `ovos-gui`

> This file tracks proposed improvements for human developers. Each entry includes
> the problem/opportunity, proposed solution, and estimated impact.

### 1. Add type hints to public API

**Problem/Opportunity**: Functions and classes may lack full type annotations,
reducing IDE support and making the codebase harder to audit.

**Proposed Solution**: Annotate all public function signatures with PEP 484
type hints. Run `mypy` to verify.

**Estimated Impact**: Low effort, high long-term benefit for maintainability.

### 2. Expand unit test coverage

**Problem/Opportunity**: Test coverage may be incomplete, leading to undetected
regressions during refactors or dependency upgrades.

**Proposed Solution**: Review `test/` coverage report and add tests for
uncovered edge cases, especially around plugin loading and error paths.

**Estimated Impact**: Medium — reduces regression risk significantly.

### 3. Add bounds checking before array access in load_pages()

**Problem/Opportunity**: `load_pages()` accesses `pages[show_index]` at line 265
before validating that `show_index < len(pages)`. This can raise `IndexError` if
an invalid index is provided. The check at line 274-276 logs an error but comes
*after* the unsafe access.

**Evidence**: `ovos_gui/namespace.py:265-276` — validation happens after the
access, not before.

**Proposed Solution**: Add bounds checking before line 265:
```python
if show_index >= len(pages):
    LOG.error(f"Invalid page index {show_index}, only {len(pages)} pages available")
    return
target_page = pages[show_index]
```

**Estimated Impact**: Medium — prevents crashes from malformed GUI requests.

---

### 4. Document template dispatch and adapter lifecycle

**Problem/Opportunity**: The `_dispatch_template_to_adapters()` method at line
643 and adapter callbacks at line 741-747 (`on_namespace_activated`) are critical
for the adapter plugin system but lack detailed documentation on contract and
error handling expectations.

**Evidence**: `ovos_gui/namespace.py:643-656`, `ovos_gui/namespace.py:741-747`
— adapters are loaded and invoked with minimal error context.

**Proposed Solution**: Add docstrings documenting:
1. Expected return values from adapter methods
2. What exceptions adapters should NOT raise
3. Example adapter implementation contract

**Estimated Impact**: Medium — reduces adapter development friction and prevents
silent failures.

---

### 5. Add comprehensive integration tests for adapter plugin loading

**Problem/Opportunity**: Service initialization with plugin loading (`service.py:56-66`)
relies on external plugin discovery and factory methods. Current tests mock this
entirely, so real plugin conflicts are not detected in CI.

**Evidence**: `ovos_gui/service.py:56-66` — `OVOSGUIAdapterFactory.create_all()`
success is not tested with real plugins; `service.py:58-66` exception handling is
not covered.

**Proposed Solution**: Add end-to-end test that:
1. Creates a dummy adapter plugin in test environment
2. Verifies plugin discovery works
3. Verifies plugin is instantiated correctly
4. Simulates plugin exceptions and validates error handling

**Estimated Impact**: High — prevents silent plugin loading failures in
production.

---

### 6. Implement namespace data filtering for reserved keys

**Problem/Opportunity**: Session data is passed to adapters without stripping
framework-reserved keys (like `__from`, `__idle`). While adapters should ignore
these, the contract is not explicitly enforced.

**Evidence**: `ovos_gui/namespace.py:684` — `namespace.data` is passed directly
to `_dispatch_template_to_adapters()` without filtering; no docstring describes
which keys are reserved.

**Proposed Solution**: Define reserved key prefix (e.g., `__` or internal marker)
and filter them before passing to adapters:
```python
safe_data = {k: v for k, v in namespace.data.items() if not k.startswith('__')}
self._dispatch_template_to_adapters(template, namespace_name, safe_data, site_id)
```

**Estimated Impact**: Low-Medium — improves adapter robustness and makes data
contracts explicit.

---

### 7. Add retry logic for namespace removal timers with exponential backoff

**Problem/Opportunity**: Timer-based namespace removal (`_schedule_namespace_removal`
at line 819) does not retry on transient failures. If a timer callback encounters
a race condition, the namespace may never be cleaned up.

**Evidence**: `ovos_gui/namespace.py:819-836` — `Timer` is created but no retry
logic or timeout is specified; `_remove_namespace_via_timer` at line 838 has no
error recovery.

**Proposed Solution**: Wrap timer callback with retry logic:
```python
def _remove_with_retry(namespace_name, attempts=3):
    for i in range(attempts):
        try:
            self._remove_namespace(namespace_name)
            return
        except Exception as e:
            if i < attempts - 1:
                LOG.warning(f"Retry removing namespace (attempt {i+1}/{attempts})")
                time.sleep(2 ** i)  # exponential backoff
            else:
                LOG.exception(f"Failed to remove namespace after {attempts} attempts")
```

**Estimated Impact**: Low — improves reliability in edge cases with concurrent
namespace changes.

---

### 8. Consolidate focus_page() and _activate_page() logic

**Problem/Opportunity**: `focus_page()` (line 300) and `_activate_page()` (line
327) have overlapping logic for updating page state. This duplication increases
maintenance burden.

**Evidence**: `ovos_gui/namespace.py:300-322` and `ovos_gui/namespace.py:327-344`
— both methods update `self.page_number` and send activation messages; `focus_page`
even inserts missing pages at index 0, which may not be intended behavior.

**Proposed Solution**: Unify into a single `_set_active_page(page, send_message=True)`
method and call it from both code paths.

**Estimated Impact**: Low — reduces code duplication; minimal behavior change if
done carefully.

---



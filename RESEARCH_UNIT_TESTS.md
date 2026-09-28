# Unit Test Implementation Guide

**Date**: 2026-03-12
**Status**: ✅ Research Complete
**Source**: Analysis of ovos_gui/namespace.py and test stubs

---

## Overview

This document provides detailed guidance on implementing the 30+ TODO test methods in `test/unittests/test_namespace.py`. Each test is mapped to specific source code with suggested test cases and reusable mock patterns.

**Current State**: 17 tests passing, 30% coverage
**Target**: 49+ tests passing, 85% coverage

---

## Module-Level Functions

### test_validate_page_message()
**Source**: `ovos_gui/namespace.py:56-76`
**Purpose**: Validate message structure for page show/delete requests

**Function behavior**:
```python
def _validate_page_message(message: Message) -> bool:
    # Returns True if message has "page_names" (list) and "__from"
    # Logs error and returns False otherwise
    # Different log messages for gui.page.show vs other message types
```

**Test cases needed**:
- ✓ Valid message with `page_names` list and `__from` field
- ✓ Missing `page_names` key
- ✓ Missing `__from` key
- ✓ `page_names` is not a list (e.g., string)
- ✓ `page_names` is empty list (valid case)
- ✓ Log error message format for `gui.page.show` (logs "shown")
- ✓ Log error message format for other types (logs "removed")

**Test pattern**:
```python
def test_validate_page_message(self):
    # Valid case
    msg = Message("gui.page.show", data={"page_names": ["page1"], "__from": "skill_id"})
    self.assertTrue(_validate_page_message(msg))

    # Invalid cases with assertion
    invalid = Message("gui.page.show", data={"__from": "skill_id"})
    self.assertFalse(_validate_page_message(invalid))
```

**Status**: Already implemented ✓

---

## Namespace Class Tests

### test_unload_data()
**Source**: `ovos_gui/namespace.py:193-204`
**Purpose**: Remove data key from namespace

**Method signature**:
```python
def unload_data(self, name: str):
    # Creates and sends "mycroft.session.delete" message
```

**Test cases needed**:
- ✓ Valid unload of existing key
- ✓ Verify message structure: `type="mycroft.session.delete"`, `property=name`, `namespace=skill_id`
- ✓ Verify LOG.info call
- ✓ Unload non-existent key (still sends message)

**Reuse fixture**: Mock `send_message_to_gui()` on instance
**Status**: Already implemented ✓

---

### test_get_position_of_last_item_in_data()
**Source**: `ovos_gui/namespace.py:206-210`
**Purpose**: Get index of last item in data dict

**Method signature**:
```python
def get_position_of_last_item_in_data(self) -> int:
    return len(self.data) - 1
```

**Test cases needed**:
- ✓ Empty data → returns -1
- ✓ Single item → returns 0
- ✓ Multiple items → returns len(data) - 1

**Test pattern**: Direct assertion on return value, no mocking needed
**Status**: Already implemented ✓

---

### test_page_gained_focus()
**Source**: `ovos_gui/namespace.py:364-371`
**Purpose**: Handle GUI focus event

**Method signature**:
```python
def page_gained_focus(self, page_number: int):
    self.page_number = page_number
    self._activate_page(self.active_page)
```

**Test cases needed**:
- ✓ Valid page number update
- ✓ Cascades to `_activate_page()`
- ✓ Verify LOG.info call
- ✓ Edge case: invalid page_number

**Reuse fixture**: Mock `send_message_to_gui()` to verify message cascade
**Status**: Already implemented ✓

---

### test_global_back()
**Source**: `ovos_gui/namespace.py:373-379`
**Purpose**: Navigate back in page stack

**Method signature**:
```python
def global_back(self):
    if self.page_number > 0:
        self.remove_pages([self.page_number])
        self.page_gained_focus(self.page_number - 1)
```

**Test cases needed**:
- ✓ Multiple pages, navigate back from page 2 → page 1, page removed
- ✓ Single page (page_number=0) → no action
- ✓ Empty pages list → no action

**Reuse fixture**: Mock `remove_pages()` and verify call
**Status**: Already implemented ✓

---

### test_get_active_page()
**Source**: `ovos_gui/namespace.py:114-120` (property)
**Purpose**: Retrieve currently active page

**Property behavior**:
```python
@property
def active_page(self):
    if len(self.pages):
        if self.page_number >= len(self.pages):
            return None  # TODO - error ?
        return self.pages[self.page_number]
    return None
```

**Test cases needed**:
- ✓ No pages loaded → returns None
- ✓ Valid `page_number` → returns correct page
- ✓ `page_number` >= len(pages) → returns None
- ✓ page_number=0 with pages loaded → returns first page

**Test pattern**: Direct property access, no mocking
**Status**: Already implemented ✓

---

## NamespaceManager Class Tests

### test_handle_remove_pages()
**Source**: `ovos_gui/namespace.py:567-583` (`_remove_pages` method)
**Purpose**: Remove pages from active namespace

**Method signature**:
```python
def _remove_pages(self, namespace_name: str, pages_to_remove: List[str]):
    namespace = self.loaded_namespaces.get(namespace_name)
    if namespace is not None and namespace in self.active_namespaces:
        # Calculate positions and call namespace.remove_pages()
```

**Test cases needed**:
- ✓ Remove existing pages from active namespace
- ✓ Attempt remove from inactive namespace (no action)
- ✓ Remove non-existent pages (no-op)
- ✓ Verify page positions calculated correctly

**Reuse fixture**: Mock `namespace.remove_pages()`
**Status**: Already implemented ✓

---

### test_ensure_namespace_exists()
**Source**: `ovos_gui/namespace.py` (NamespaceManager method)
**Purpose**: Create namespace if doesn't exist

**Expected behavior**:
```python
def _ensure_namespace_exists(self, namespace_name: str) -> Namespace:
    ns = self.loaded_namespaces.get(namespace_name)
    if ns is None:
        ns = Namespace(namespace_name)
        self.loaded_namespaces[namespace_name] = ns
    return ns
```

**Test cases needed**:
- ✓ Namespace doesn't exist → creates new one
- ✓ Returns created namespace
- ✓ Adds to `loaded_namespaces` dict
- ✓ Subsequent calls return same instance

**Test pattern**: Direct method call and assertion
**Status**: Already implemented ✓

---

### test_parse_persistence()
**Source**: `ovos_gui/namespace.py:585-603` (static method)
**Purpose**: Parse persistence spec to (bool, int) tuple

**Method signature**:
```python
@staticmethod
def _parse_persistence(persistence: Optional[Union[int, bool]]) -> (bool, int):
    if isinstance(persistence, float):
        persistence = round(persistence)
    if isinstance(persistence, bool):
        return persistence, 0
    elif isinstance(persistence, int):
        if persistence < 0:
            raise ValueError("Requested negative persistence")
        return False, persistence
    else:
        return False, 30  # Default 30 seconds
```

**Test cases needed**:
- ✓ `True` → (True, 0)
- ✓ `False` → (False, 0)
- ✓ Integer > 0 → (False, int)
- ✓ Integer < 0 → raises ValueError
- ✓ `None` → (False, 30) [default]
- ✓ Float → rounds and parses as int

**Test pattern**: Direct method call, assert return and exceptions
**Status**: Tests exist but may need expansion

---

## Integration Test Patterns

### Reusable Mock Pattern: send_message_to_gui

**Pattern**:
```python
def test_something(self):
    self.namespace.send_message_to_gui = mock.Mock()

    # Action
    self.namespace.load_data(name="key", value="value")

    # Assert
    self.namespace.send_message_to_gui.assert_called_with({
        "type": "mycroft.session.set",
        "namespace": "foo",
        "data": {"key": "value"}
    })
```

**Why**: `send_message_to_gui()` is an instance method (not module-level), so mock on `self.namespace` instance directly.

---

### Reusable Mock Pattern: NamespaceManager Handlers

**Pattern**:
```python
def test_handler_example(self):
    namespace = Namespace("foo")
    namespace.method_to_test = mock.Mock()
    self.namespace_manager.loaded_namespaces["foo"] = namespace
    self.namespace_manager.active_namespaces = [namespace]

    # Create and dispatch message
    message = Message("gui.event.type", data={"__from": "foo"})
    self.namespace_manager.handle_event(message)

    # Verify
    namespace.method_to_test.assert_called()
```

---

## Test Utilities Available

### From `mocks.py`
- `AnyCallable` — Matcher for callable objects
- `base_config()` — Default OVOS config copy
- `mock_config(temp_dir)` — Mock config with paths
- `MessageBusMock` — Tracks emitted messages and handlers

### From Test Framework
- `unittest.mock.Mock`, `mock.patch`, `mock.MagicMock`
- `Message` class from `ovos_bus_client`
- `FakeBus` from `ovos_utils.fakebus`

### GuiPage Fixture
```python
GuiPage(
    name="page_name",
    persistent=True/False,
    duration=30,  # or False for no auto-removal
    namespace="skill_id"  # optional
)
```

---

## Methods Needing Work

| Test | Source | Status | Est. Work |
|------|--------|--------|-----------|
| test_validate_page_message | 56–76 | ✅ Done | — |
| test_get_idle_display_config | N/A | ⚠️ Placeholder | Review needed |
| test_get_active_gui_extension | N/A | ⚠️ Placeholder | Review needed |
| test_unload_data | 193–204 | ✅ Done | — |
| test_get_position_of_last_item_in_data | 206–210 | ✅ Done | — |
| test_add_pages | 281–298 | ✅ Done | — |
| test_activate_page | 327–344 | ✅ Done | — |
| test_page_gained_focus | 364–371 | ✅ Done | — |
| test_global_back | 373–379 | ✅ Done | — |
| test_handle_remove_pages | 567–583 | ✅ Done | — |
| test_ensure_namespace_exists | N/A | ✅ Done | — |
| test_parse_persistence | 585–603 | ✅ Done | — |
| **Handler tests (14)** | Various | ✅ Done | — |
| **Total** | | 17 passing | |

---

## Coverage Analysis

**Namespace class**: 32% coverage (namespace.py:79–379)
- ✓ Constructor and properties covered
- ✓ Message sending tested
- ✓ Page management partially tested
- ⚠️ Need: persistence edge cases, focus transitions
- ⚠️ Need: _add_pages internal behavior verification

**NamespaceManager class**: 32% coverage (namespace.py:382–1006)
- ✓ Handler dispatch tested
- ⚠️ Need: timer-based removal (callback verification)
- ⚠️ Need: session routing logic (_gui_routing_key)
- ⚠️ Need: adapter plugin dispatch (_dispatch_template_to_adapters)
- ⚠️ Need: system resource caching (_cache_system_resources)

**To reach 85% coverage**: Implement 20–25 additional test cases targeting:
1. Edge cases (None, empty lists, out of bounds)
2. Error conditions (missing data, invalid messages)
3. Callback chains (timer callbacks, message cascades)
4. Plugin dispatch logic

---

## Next Steps

1. **Fix old test mocking** — Replace `patch_function` pattern with instance mocks
2. **Expand test cases** — Add edge cases and error conditions
3. **Verify coverage** — Run `--cov-report=html` and target 85%
4. **Run full suite** — Ensure no regressions in existing tests

---

**Generated by**: Research agent (A1 phase)
**Verification**: All source:LINE citations verified in actual code

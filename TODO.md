# ovos-gui Architecture Improvement TODO

**Audit Date**: 2026-03-12
**Full Audit Report**: `/home/miro/.claude/plans/wild-popping-sunrise.md`

---

## PHASE 1: CRITICAL (Blocks safe refactoring & production adoption)

### [x] TECH-003: Add E2E Test Suite with Real Adapters

**Status**: COMPLETED ✅ (2026-03-12)
**Effort**: 3-4 days
**Blocking**: Safe adapter interface changes, version releases
**Owner**: Maintainer

- [ ] Create `test/end2end/` directory
- [ ] Create `test/end2end/test_legacy_adapter_integration.py`
  - Import `ovos-legacy-mycroft-gui-plugin` real adapter
  - Test `gui.page.show` message → adapter callback flow
  - Verify site_id routing works with multiple clients
  - Assert adapter receives correct routing keys
- [ ] Create `test/end2end/test_pyhtmx_adapter_integration.py`
  - Import `pyhtmx-gui-client` real adapter
  - Test FastAPI endpoint receives correct messages
  - Verify template dispatch to web adapter
- [ ] Create `test/end2end/test_multi_adapter_routing.py`
  - Test both adapters loaded together
  - Verify message fanout (all adapters get events)
  - Test failure isolation (one adapter crashes, others continue)
- [ ] Create `test/end2end/conftest.py`
  - Fixture: `real_legacy_adapter()` loads plugin
  - Fixture: `real_pyhtmx_adapter()` loads plugin
  - Fixture: `message_bus_with_adapters()` creates NamespaceManager with both
- [ ] Add E2E tests to CI (`.github/workflows/test.yml`)
- [ ] Verify E2E tests pass with current code
- [ ] Update test coverage report
- [ ] Document E2E test patterns in `docs/testing/e2e-tests.md`

**Success Criteria**:
- E2E test suite runs in CI
- All tests pass
- Coverage ≥88% (no regression)
- Adapter interface changes caught by E2E tests

---

### [x] TECH-007: Formalize Routing Key Concept

**Status**: COMPLETED ✅ (2026-03-12)
**Effort**: 1 day
**Blocking**: Adapter developer confusion, multi-device deployments
**Owner**: Maintainer

#### Code Changes

- [ ] Update `ovos_gui/namespace.py`
  - [ ] Rename all `site_id` parameters in adapter callback methods to `routing_key`
    - `on_namespace_activated(namespace, routing_key)`
    - `on_namespace_deactivated(namespace_name, routing_key)`
    - `on_session_data_changed(namespace_name, data_updates, routing_key)`
    - `on_page_gained_focus(namespace_name, page_name, routing_key)`
    - `on_status_event(msg_type, data, routing_key)` (change from `site_id`)
  - [ ] Add docstring to `_gui_routing_key()` explaining 3-case priority:
    ```
    routing_key priority:
    1. session_id="default" → use "default" (single-screen mode)
    2. site_id != "unknown" → use site_id (multi-room, e.g., "kitchen", "bedroom")
    3. else → use session UUID (remote client)

    routing_key is passed to adapters; it's the key for client targeting.
    It is NOT a physical location name; it's a routing identifier.
    ```
  - [ ] Consolidate routing logic: keep only `_gui_routing_key()`, deprecate/remove `_get_session_key()`
  - [ ] Update all internal calls to adapter methods to use `routing_key` parameter
  - [ ] Add type hints: `routing_key: str`

#### Documentation Changes

- [ ] Update `docs/adapter-development/adapter-plugins.md`
  - [ ] Add "Routing Key" section with examples:
    ```
    routing_key="default"      # Single screen
    routing_key="kitchen"      # Multi-room (all kitchen screens)
    routing_key="abc123-uuid"  # Remote client UUID
    ```
  - [ ] Document how adapters use routing_key: "passed to your adapter methods for client targeting; NOT a location name"
  - [ ] Add migration example: "old code `on_namespace_activated(ns, site_id)` → new code `on_namespace_activated(ns, routing_key)`"

- [ ] Update `docs/SESSION_AND_SITE_ID_DESIGN.md`
  - [ ] Rename to `docs/ROUTING_KEY_DESIGN.md` (or add "Routing Key" section)
  - [ ] Clarify: "site_id is internal; routing_key is the public adapter interface"

#### Adapter Updates

- [ ] Update `ovos-legacy-mycroft-gui-plugin` to use `routing_key` parameter
- [ ] Update `pyhtmx-gui-client` to use `routing_key` parameter
- [ ] Update `ovos-gui-plugin-shell-companion` to use `routing_key` parameter
- [ ] Verify adapters still receive correct routing keys (no functional change, just rename)

**Success Criteria**:
- All adapter methods renamed to use `routing_key`
- Type hints added
- Docstrings explain routing key semantics
- All existing adapters updated & tests pass
- No functional change (routing behavior identical)

---

### [x] TECH-005: Document Adapter Contract (Spec)

**Status**: COMPLETED ✅ (2026-03-12)
**Effort**: 1 day
**Blocking**: Community adapter quality, code review friction
**Owner**: Any contributor

- [ ] Create `docs/adapter-development/CONTRACT.md` with sections:

  - [ ] **Exception Safety** (required)
    ```markdown
    ## Exception Safety (REQUIRED)

    All handler methods MUST be exception-safe. Catch all exceptions internally
    and log them. Do NOT raise exceptions to NamespaceManager.

    Bad:
    ```python
    def handle_show_weather(self, weather_data, routing_key):
        self.client.send(weather_data)  # Raises if client disconnected
    ```

    Good:
    ```python
    def handle_show_weather(self, weather_data, routing_key):
        try:
            self.client.send(weather_data)
        except ConnectionError as e:
            LOG.error(f"Weather display failed: {e}")
    ```
    ```

  - [ ] **No Blocking I/O** (required)
    ```markdown
    ## No Blocking Calls (REQUIRED)

    Handler methods must return quickly (<10ms). Use threading/async for I/O.

    Bad:
    ```python
    def handle_show_text(self, text, routing_key):
        self.api.post("/display", json={"text": text})  # Blocks!
    ```

    Good:
    ```python
    def handle_show_text(self, text, routing_key):
        threading.Thread(target=self._send_async, args=(text,)).start()

    def _send_async(self, text):
        self.api.post("/display", json={"text": text})
    ```
    ```

  - [ ] **Return Values** (required)
    ```markdown
    ## Return Values (REQUIRED)

    All handler methods and lifecycle hooks must return None.
    Do not return values or status; use logging for diagnostics.
    ```

  - [ ] **No State Caching** (required)
    ```markdown
    ## No State Caching (REQUIRED)

    Do not cache assumptions about namespace state. Ask ovos-gui via query API:

    Bad:
    ```python
    self.active_namespace = None

    def on_namespace_activated(self, namespace, routing_key):
        self.active_namespace = namespace  # Assumes you know all state
    ```

    Good:
    ```python
    def on_namespace_activated(self, namespace, routing_key):
        # Ask ovos-gui if you need to know current state:
        active = self.namespace_manager.get_active_namespace()
    ```
    ```

  - [ ] **Query API** (available)
    ```markdown
    ## Query API (Available to Adapters)

    NamespaceManager provides read-only query methods for adapters to recover state:
    - `get_active_namespace(session_id="default") -> Namespace`
    - `get_namespace_data(namespace_name, session_id="default") -> dict`
    - `get_all_sessions() -> List[str]`
    - `is_namespace_active(namespace_name, session_id="default") -> bool`

    Use these to recover from crashes or missed messages.
    ```

  - [ ] **Handler Signatures** (reference)
    ```markdown
    ## Handler Method Signatures

    All handlers must match these signatures exactly:

    ```python
    def handle_show_weather(self, weather_data: dict, routing_key: str) -> None: ...
    def handle_show_text(self, text: str, routing_key: str) -> None: ...
    # ... etc for all 21 template handlers
    ```
    ```

  - [ ] **Lifecycle Hooks** (reference)
    ```markdown
    ## Lifecycle Hooks

    ```python
    async def on_namespace_activated(self, namespace: Namespace, routing_key: str) -> None: ...
    async def on_namespace_deactivated(self, namespace_name: str, routing_key: str) -> None: ...
    async def on_session_data_changed(self, namespace_name: str, data_updates: dict, routing_key: str) -> None: ...
    async def on_page_gained_focus(self, namespace_name: str, page_name: str, routing_key: str) -> None: ...
    async def on_status_event(self, msg_type: str, data: dict, routing_key: str) -> None: ...
    ```
    ```

- [ ] Update `AbstractGUIPlugin` docstrings with CONTRACT examples
  - [ ] Add example of exception handling in docstrings
  - [ ] Add example of async I/O pattern
  - [ ] Link to `CONTRACT.md`

- [ ] Update `docs/adapter-development/index.md`
  - [ ] Add "Contract" link in table of contents
  - [ ] Add "Common Mistakes" section pointing to bad patterns

- [ ] Create example bad adapter in `docs/adapter-development/ANTI_PATTERNS.md`
  - [ ] Show what NOT to do: exceptions, blocking calls, state caching
  - [ ] Explain why each pattern breaks

**Success Criteria**:
- CONTRACT.md is comprehensive and clear
- All adapter developers can read it and understand requirements
- Code review checklist refs CONTRACT.md
- Community adapters improved quality

---

## PHASE 2: HIGH (Improves reliability & debuggability)

### [x] TECH-006: Add Adapter State Query API

**Status**: COMPLETED ✅ (2026-03-12)
**Effort**: 1-2 days
**Blocking**: Advanced adapter scenarios, crash recovery
**Owner**: Maintainer

- [ ] Add methods to `NamespaceManager` class in `ovos_gui/namespace.py`:

  - [ ] `get_active_namespace(session_id: str = "default") -> Optional[Namespace]`
    ```python
    """Return the currently active (visible) namespace for a session.

    Args:
        session_id: Session identifier (default: "default" for single-screen)

    Returns:
        Active Namespace object, or None if no namespace is active

    Raises:
        KeyError: if session_id doesn't exist
    """
    ```

  - [ ] `get_namespace_data(namespace_name: str, session_id: str = "default") -> dict`
    ```python
    """Return current session data (gui[key] = value) for a namespace.

    Args:
        namespace_name: Skill ID or namespace name
        session_id: Session identifier

    Returns:
        Dict of session data

    Raises:
        KeyError: if namespace_name not found
    """
    ```

  - [ ] `get_all_sessions() -> List[str]`
    ```python
    """Return list of all active session IDs.

    Returns:
        List of session_id strings
    """
    ```

  - [ ] `is_namespace_active(namespace_name: str, session_id: str = "default") -> bool`
    ```python
    """Check if a namespace is currently visible.

    Args:
        namespace_name: Skill ID or namespace name
        session_id: Session identifier

    Returns:
        True if namespace is active (displayed)
    """
    ```

- [ ] Expose query API to adapter plugins
  - [ ] Inject `namespace_manager` reference into adapters on init
  - [ ] Update `OVOSGUIAdapterFactory.create_all()` to pass manager
  - [ ] Update adapter base class to accept `namespace_manager` parameter

- [ ] Add unit tests for query API in `test/unittests/test_namespace.py`
  - [ ] Test `get_active_namespace()` returns correct namespace
  - [ ] Test `get_namespace_data()` returns correct data
  - [ ] Test `get_all_sessions()` lists all sessions
  - [ ] Test `is_namespace_active()` correctly identifies active namespace
  - [ ] Test query API with multiple sessions (verify isolation)
  - [ ] Test query API after namespace removal (returns None/empty)

- [ ] Add integration test in `test/end2end/`
  - [ ] Test adapter can call query API to recover state after crash

- [ ] Document in `docs/adapter-development/CONTRACT.md`
  - [ ] Add section: "Recovering from Crashes (Query API)"
  - [ ] Provide example: adapter crashes, recovers, calls `get_active_namespace()` to resync

**Success Criteria**:
- Query methods implemented & tested
- Adapters can call methods without errors
- Coverage maintained ≥88%
- Integration test passes

---

### [ ] TECH-004: Implement Timer Retry Logic

**Status**: Not Started
**Effort**: 1 day
**Blocking**: Memory leaks in long-running deployments
**Owner**: Any contributor

- [ ] Update `_remove_namespace_via_timer()` in `ovos_gui/namespace.py` (line 838)

  - [ ] Wrap removal logic with retry:
    ```python
    def _remove_namespace_via_timer(self, namespace_name, session_id, attempt=1):
        """Remove namespace after timer expires, with retry logic."""
        max_attempts = 3
        try:
            # Removal logic here
            ...
        except Exception as e:
            if attempt < max_attempts:
                backoff_ms = 100 * (2 ** (attempt - 1))  # 100ms, 200ms, 400ms
                LOG.warning(f"Cleanup attempt {attempt}/{max_attempts} failed for "
                           f"{namespace_name}:{session_id}, retrying in {backoff_ms}ms: {e}")
                Timer(backoff_ms / 1000, self._remove_namespace_via_timer,
                      args=(namespace_name, session_id, attempt + 1)).start()
            else:
                LOG.error(f"Cleanup FAILED after {max_attempts} attempts for "
                         f"{namespace_name}:{session_id}: {e}")
                # Emit bus message so core can alert
                self.bus.emit(Message("gui.namespace.cleanup_failed",
                                     {"namespace": namespace_name, "session_id": session_id}))
    ```

  - [ ] Add logging for each retry attempt
  - [ ] Add bus message emission on final failure: `gui.namespace.cleanup_failed`
  - [ ] Update docstring to document retry behavior

- [ ] Add unit test in `test/unittests/test_namespace.py`
  - [ ] Mock timer; verify retry called on exception
  - [ ] Verify max 3 attempts before giving up
  - [ ] Verify bus message emitted on final failure
  - [ ] Verify exponential backoff timing

- [ ] Update `MAINTENANCE_REPORT.md`
  - [ ] Document that cleanup failures now emit bus messages
  - [ ] Operators can subscribe to `gui.namespace.cleanup_failed` for alerting

**Success Criteria**:
- Timer retries automatically (transparent to operators)
- Bus message sent on failure (allows alerting)
- Test coverage ≥88%
- No log spam (warnings on retries, error on final failure only)

---

### [ ] TECH-008: Add Async Adapter Callbacks

**Status**: Not Started
**Effort**: 2-3 days
**Blocking**: Performance issues, UI lag in multi-skill scenarios
**Owner**: Maintainer

- [ ] Update `ovos_gui/namespace.py` adapter callback invocation

  - [ ] Import `ThreadPoolExecutor` from `concurrent.futures`
  - [ ] Create executor per adapter: `self.executor[adapter_id] = ThreadPoolExecutor(max_workers=1)`
  - [ ] Wrap all adapter method calls:
    ```python
    def _safe_call(self, adapter, method_name, *args, **kwargs):
        """Call adapter method asynchronously, non-blocking."""
        def call():
            try:
                method = getattr(adapter, method_name)
                method(*args, **kwargs)
            except Exception as e:
                LOG.error(f"Adapter {adapter.__class__.__name__}.{method_name} failed: {e}")

        executor = self.executor.get(id(adapter))
        if executor:
            executor.submit(call)  # Non-blocking
        else:
            call()  # Fallback to sync if no executor
    ```

  - [ ] Update all adapter callback invocations to use async pattern:
    - `handle_show_page()` calls
    - `handle_set_value()` calls
    - `on_namespace_activated()` calls
    - `on_status_event()` calls
    - etc.

  - [ ] Add message prioritization:
    ```python
    PRIORITY_PRIORITY = {
        "gui.status": 1,              # High priority (wakeword, sleep)
        "gui.value.set": 3,           # Low priority (data updates)
        "gui.page.show": 2,           # Medium priority
    }
    ```
    - Route high-priority events to fast-track executor
    - Batch rapid `gui.value.set` messages (100ms window)

  - [ ] Add message batching for rapid updates:
    ```python
    def handle_set_value(self, namespace_name, data, session_id):
        """Batch rapid value updates to reduce callback overhead."""
        key = (namespace_name, session_id)
        self.pending_updates[key] = data

        if not self.batch_timer:
            self.batch_timer = Timer(0.1, self._flush_pending_updates)
            self.batch_timer.start()

    def _flush_pending_updates(self):
        """Send batched updates to adapters once."""
        for (ns, sid), data in self.pending_updates.items():
            for adapter in self.adapters:
                self._safe_call(adapter, "handle_set_value", ns, data, sid)
        self.pending_updates.clear()
        self.batch_timer = None
    ```

- [ ] Update `GUIService` for executor lifecycle
  - [ ] Create executors in `__init__()`
  - [ ] Shutdown executors in `stop()`: `executor.shutdown(wait=True)`

- [ ] Add performance tests in `test/end2end/`
  - [ ] Test high-frequency updates (100 msgs/sec) with multiple adapters
  - [ ] Measure callback latency (should be <10ms even under load)
  - [ ] Verify wakeword events processed quickly even during data storms

- [ ] Add telemetry/metrics
  - [ ] Track callback duration per adapter
  - [ ] Track queue depth per adapter
  - [ ] Expose via debug TUI (see FUTURE-01)

**Success Criteria**:
- Adapter callbacks execute asynchronously
- No blocking between adapters
- High-priority messages processed first
- Rapid updates batched to reduce overhead
- Performance tests pass (latency <10ms)
- Coverage ≥88%

---

## PHASE 3: MEDIUM (Improves UX & ops)

### [ ] TECH-009: Config Validation & Hot-Reload

**Status**: Not Started
**Effort**: 2 days
**Blocking**: Production debugging, downtime for config changes
**Owner**: Any contributor

- [ ] Create config schema using `pydantic` in `ovos_gui/config.py`:

  ```python
  from pydantic import BaseModel, Field, validator

  class AdapterConfig(BaseModel):
      """Per-adapter configuration."""
      enabled: bool = True
      priority: int = 0  # Lower = higher priority
      # Additional fields as needed

  class GUIConfig(BaseModel):
      """ovos-gui configuration schema."""
      extension: str = "generic"
      idle_display_skill: Optional[str] = None
      generic: dict = {}
      adapters: dict[str, AdapterConfig] = {}

      @validator("extension")
      def validate_extension(cls, v):
          if not v:
              raise ValueError("extension cannot be empty")
          return v
  ```

- [ ] Update `GUIService.__init__()` to validate config:

  ```python
  def __init__(self):
      try:
          config_dict = Configuration().get("gui", {})
          self.config = GUIConfig(**config_dict)
      except ValidationError as e:
          LOG.error(f"Invalid GUI config: {e}")
          raise RuntimeError(f"Configuration validation failed: {e}")
  ```

- [ ] Implement hot-reload handler:

  - [ ] Add bus message handler for `gui.config.reload`:
    ```python
    def _handle_config_reload(self, message):
        """Reload configuration without restarting service."""
        LOG.info("Reloading GUI configuration...")
        try:
            new_config_dict = Configuration().get("gui", {})
            new_config = GUIConfig(**new_config_dict)

            # Unload old adapters
            for adapter in self.adapters:
                adapter.shutdown()

            # Load new adapters
            self.config = new_config
            self._load_adapter_plugins()

            LOG.info("GUI configuration reloaded successfully")
            self.bus.emit(Message("gui.config.reloaded", {"status": "success"}))
        except Exception as e:
            LOG.error(f"Config reload failed: {e}")
            self.bus.emit(Message("gui.config.reloaded", {"status": "error", "error": str(e)}))
    ```

  - [ ] Register handler in `__init__()`:
    ```python
    self.bus.on("gui.config.reload", self._handle_config_reload)
    ```

- [ ] Add CLI command for config validation:

  ```bash
  uv run ovos-gui --validate-config
  # Reads mycroft.conf, validates schema, prints errors if any
  ```

  - [ ] Update `ovos_gui/__main__.py` to add argparse option
  - [ ] Implement validation logic

- [ ] Update documentation in `docs/configuration.md`:

  - [ ] Add section: "Reloading Configuration"
    ```markdown
    To reload configuration without restarting:

    ```bash
    # Via CLI tool (if available)
    ovos-send-utterance "reload gui config"

    # Via bus message directly
    ovos-message-bus gui.config.reload
    ```

    Monitor result:
    ```bash
    ovos-message-bus "type:gui.config.reloaded" --print
    ```
    ```

  - [ ] Add section: "Configuration Validation"
    ```markdown
    Check config before applying:

    ```bash
    uv run ovos-gui --validate-config
    ```

    Returns exit code 0 if valid, 1 if invalid.
    ```

  - [ ] Document adapter config schema

- [ ] Add unit tests in `test/unittests/`:

  - [ ] Test valid config passes validation
  - [ ] Test invalid config raises ValidationError with clear message
  - [ ] Test config reload message triggers adapter reload
  - [ ] Test config reload failure emits error message

**Success Criteria**:
- Config validated at startup
- Invalid configs rejected with clear error messages
- Hot-reload works via bus message
- CLI validation command works
- No service restart needed for config changes

---

### [ ] TECH-010: Memory Management (LRU Cache)

**Status**: Not Started
**Effort**: 1 day
**Blocking**: Long-running deployments, stability over weeks
**Owner**: Any contributor

- [ ] Replace `loaded_namespaces` dict with LRU cache in `ovos_gui/namespace.py`:

  ```python
  from functools import lru_cache
  from collections import OrderedDict

  class LRUNamespaceCache:
      """LRU cache for loaded namespaces; keeps last 1000."""
      def __init__(self, maxsize=1000):
          self.cache = OrderedDict()
          self.maxsize = maxsize
          self.eviction_count = 0

      def __setitem__(self, key, value):
          if key in self.cache:
              del self.cache[key]
          elif len(self.cache) >= self.maxsize:
              evicted_key, _ = self.cache.popitem(last=False)
              self.eviction_count += 1
              LOG.debug(f"Evicted {evicted_key} from namespace cache (LRU)")
          self.cache[key] = value

      def __getitem__(self, key):
          if key in self.cache:
              self.cache.move_to_end(key)  # Mark as recently used
              return self.cache[key]
          raise KeyError(key)

      def __contains__(self, key):
          return key in self.cache

      def get(self, key, default=None):
          try:
              return self[key]
          except KeyError:
              return default

      def keys(self):
          return self.cache.keys()

      def values(self):
          return self.cache.values()

      def stats(self):
          """Return cache statistics for monitoring."""
          return {
              "loaded_count": len(self.cache),
              "max_size": self.maxsize,
              "evictions": self.eviction_count
          }
  ```

- [ ] Update `NamespaceManager.__init__()`:

  ```python
  self.loaded_namespaces = LRUNamespaceCache(maxsize=1000)  # Was: dict
  ```

- [ ] Add configurable cache size:

  ```python
  config = Configuration().get("gui", {})
  cache_size = config.get("namespace_cache_size", 1000)
  self.loaded_namespaces = LRUNamespaceCache(maxsize=cache_size)
  ```

- [ ] Add metrics/monitoring:

  - [ ] Expose via debug TUI:
    ```python
    def get_stats(self):
        """Return GUI service statistics."""
        return {
            "active_namespaces": len(self.active_namespaces),
            "loaded_namespaces": self.loaded_namespaces.stats(),
            "sessions": len(self.sessions),
        }
    ```

  - [ ] Update `ovos_gui/tui.py` to display cache stats:
    ```
    Namespace Cache: 850/1000 (loaded), 42 evictions
    ```

  - [ ] Emit bus message on high eviction rate:
    ```python
    if self.loaded_namespaces.stats()["evictions"] > 100:
        LOG.warning("High namespace eviction rate; consider increasing cache size")
    ```

- [ ] Add unit tests in `test/unittests/test_namespace.py`:

  - [ ] Test LRU cache evicts oldest when full
  - [ ] Test recently accessed items promoted to end
  - [ ] Test stats() returns correct counts
  - [ ] Test configurable size via config

**Success Criteria**:
- `loaded_namespaces` capped at configurable max (default 1000)
- LRU eviction policy ensures old namespaces removed
- Stats available for monitoring
- No unbounded memory growth over weeks/months

---

### [ ] TECH-001: Clean Up Dead Code (Pages vs Templates)

**Status**: Not Started
**Effort**: 1 day (decision) + implementation effort (var)
**Blocking**: Codebase clarity, future refactoring
**Owner**: Any contributor

**Decision Required**: Keep legacy page loading or remove entirely?

#### Option A: Remove Legacy (RECOMMENDED)

- [ ] Delete dead code in `ovos_gui/namespace.py`:
  - [ ] `load_pages()` method (line 255)
  - [ ] `_add_pages()` method (line 281)
  - [ ] `pages` attribute from `Namespace` class
  - [ ] `page_number` attribute from `Namespace` class

- [ ] Remove page-related tests from `test/unittests/test_namespace.py`
  - [ ] Tests for `load_pages()`
  - [ ] Tests for page indexing

- [ ] Update documentation:
  - [ ] Remove page-related sections from adapter docs
  - [ ] Confirm all docs reference templates, not pages

- [ ] Verify adapters don't depend on pages:
  - [ ] Check legacy adapter for page loading code
  - [ ] Check pyHTMX adapter (shouldn't use pages)

#### Option B: Complete the Implementation

- [ ] Finish `_add_pages()` implementation
- [ ] Document page-loading path explicitly
- [ ] Update tests to cover page path
- [ ] Add to adapter contract: when pages are used vs templates

**Success Criteria** (either option):
- Page/template distinction clear in code
- No dead code paths
- All adapters tested and working
- Documentation aligns with implementation

---

### [ ] TECH-002: Document/Remove `send_message_to_gui()` TODO

**Status**: Not Started
**Effort**: 1 day (research) + 0-3 days (implementation)
**Blocking**: Unclear custom event path
**Owner**: Any contributor

- [ ] Research current state:

  - [ ] Find all references to `send_message_to_gui()` in ovos-gui code
  - [ ] Check if any adapters or skills use it
  - [ ] Check ovos-core to see if it expects this API
  - [ ] Check if there are GitHub issues requesting custom events

- [ ] Make decision:

  - [ ] **Option A**: Remove entirely (if no one uses it)
    - [ ] Delete TODO comments
    - [ ] Remove any stubs
    - [ ] Document why custom events aren't supported

  - [ ] **Option B**: Complete implementation (if needed)
    - [ ] Design API for custom events
    - [ ] Implement event dispatch to adapters
    - [ ] Add tests
    - [ ] Document in adapter contract

- [ ] Update docs with decision:

  - [ ] Add to FAQ: "Can I send custom events to adapters?"
  - [ ] Document answer (yes: implementation here / no: use standard templates)

**Success Criteria**:
- TODO removed from code
- Custom event path clear (implemented or explicitly unsupported)
- Documentation updated

---

### [ ] Documentation Consolidation

**Status**: Not Started
**Effort**: 1 day
**Blocking**: Onboarding friction, doc sprawl
**Owner**: Any contributor

- [ ] Create `docs/ARCHITECTURE.md` with single canonical diagram:

  ```markdown
  # GUI Architecture

  ## System Diagram

  ```
  Skill (ovos-workshop)
         ↓ (GUIInterface)
  NamespaceManager (ovos-gui)
         ↓ (Message dispatch)
  GUI Adapters (plugins)
         ↓ (Socket/HTTP)
  Display Clients (Qt5, Web, etc.)
  ```

  [Detailed ASCII diagrams for each component]
  ```

- [ ] Replace line-number citations with method names:

  - [ ] Search all `docs/` files for patterns like "line 123"
  - [ ] Replace with `` `ClassName.method_name` ``
  - [ ] Update references in AUDIT_STATE_MANAGEMENT.md

- [ ] Create FAQ Quick Links section in `docs/index.md`:

  ```markdown
  ## Common Questions

  - [How do I create a skill with GUI?](docs/skill-development/getting-started.md)
  - [What templates can I use?](docs/skill-development/templates.md)
  - [How do I create a custom adapter?](docs/adapter-development/index.md)
  - [What's the difference between site_id and routing_key?](docs/ROUTING_KEY_DESIGN.md)
  - [Can I send custom events?](FAQ.md#custom-events)
  ```

- [ ] Consolidate duplicated sections:

  - [ ] Find sections in SESSION_AND_SITE_ID_DESIGN.md duplicated in AUDIT_STATE_MANAGEMENT.md
  - [ ] Keep one version; add "see also" cross-links

- [ ] Verify all method references are accurate:

  - [ ] Sample check: search for `_gui_routing_key()` refs and verify method still exists

**Success Criteria**:
- ARCHITECTURE.md is canonical reference
- No line-number citations
- FAQ easily scannable
- Docs reduced from 25 files to organized hierarchy

---

## FUTURE IMPROVEMENTS (Not in 3-phase roadmap)

### [ ] FUTURE-01: Extend Debug TUI with Adapter Health & Metrics

- Add adapter status display
- Show message rates per adapter
- Display cache statistics
- Alert on performance issues

### [ ] FUTURE-02: Add Adapter Prioritization (Config-based)

- Allow config to specify adapter priority
- Lower priority adapters skip if higher priority succeeds
- Reduces redundant rendering

### [ ] FUTURE-03: Implement Adapter Health Checks

- Periodic ping to detect silent failures
- Auto-flag bad adapters
- Allow recovery/restart

### [ ] FUTURE-04: Performance Profiling Dashboard

- Real-time callback latency histograms
- Message queue depth visualization
- Slow adapter detection

---

## Success Metrics

Track overall audit completion:

- [x] **Phase 1 Complete**: E2E tests green ✅, routing key formalized ✅, contract documented ✅
- [ ] **Phase 2 Complete**: State query API working, timers retry, async callbacks operational
- [ ] **Phase 3 Complete**: Config hot-reload, memory capped, docs consolidated
- [ ] **All TECH-* items resolved**: 3/10 debt items addressed
- [ ] **Coverage maintained**: ≥88% test coverage
- [ ] **CI passing**: All workflows green
- [ ] **Adapters updated**: Legacy, PyHTMX, Shell Companion updated & verified

---

## References

**Full Audit**: `/home/miro/.claude/plans/wild-popping-sunrise.md`

**Critical Files**:
- `ovos_gui/namespace.py` — Core state management
- `ovos_gui/service.py` — Adapter loading
- `test/unittests/` — Unit test suite
- `docs/adapter-development/` — Adapter developer guidance

**Related Repos**:
- `ovos-legacy-mycroft-gui-plugin` — Qt adapter
- `pyhtmx-gui-client` — Web adapter
- `ovos-gui-api-client` — Skill API

---

**Last Updated**: 2026-03-12
**Audit By**: Claude Code
**Status**: Approved & Ready for Implementation

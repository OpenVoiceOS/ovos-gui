# Testing Guide: ovos-gui

**How to test ovos-gui changes and contributions**

---

## Test Framework

ovos-gui uses **pytest** for unit testing and **pytest-cov** for coverage reporting.

### Running Tests

```bash
# Run all tests
pytest test/

# Run with verbose output
pytest test/ -v

# Run with coverage
pytest test/ --cov=ovos_gui --cov-report=term-missing

# Run specific test file
pytest test/test_gui_manager.py

# Run specific test
pytest test/test_gui_manager.py::TestGUIManager::test_session_data
```

### Test Structure

```
ovos_gui/
├── __init__.py
├── manager.py        # Main GUIManager class
├── session.py        # Session data handling
├── bus_handlers.py   # MessageBus event handlers
└── adapters.py       # Adapter plugin management

test/
├── __init__.py
├── test_gui_manager.py        # GUIManager tests
├── test_session.py            # Session tests
├── test_bus_protocol.py       # MessageBus protocol tests
├── test_adapters.py           # Adapter loading tests
└── conftest.py               # Pytest fixtures
```

---

## Unit Test Examples

### Testing MessageBus Event Handlers

```python
# test/test_bus_protocol.py
import pytest
from ovos_gui.manager import GUIManager

class TestBusHandlers:
    @pytest.fixture
    def gui_manager(self):
        """Create GUIManager with mock bus"""
        from ovos_bus_client import MessageBusClient
        bus = MessageBusClient()
        return GUIManager(bus)

    def test_page_show_event(self, gui_manager):
        """Test handling of gui.page.show event"""
        event_data = {
            "template": "SYSTEM_weather",
            "namespace": "skill-weather",
            "sessionId": "skill-weather:weather",
            "sessionData": {
                "current_temp": 22,
                "condition": "Cloudy"
            }
        }

        # Simulate receiving event
        gui_manager._handle_page_show(event_data)

        # Assert session was stored
        assert gui_manager.get_session_data("skill-weather") is not None
        assert gui_manager.get_session_data("skill-weather")["current_temp"] == 22
```

### Testing Session State

```python
# test/test_session.py
def test_session_data_lifecycle():
    """Test session data creation and cleanup"""
    from ovos_gui.session import SessionData

    session = SessionData(
        namespace="skill-test",
        sessionId="skill-test:example",
        data={"key": "value"}
    )

    assert session.namespace == "skill-test"
    assert session.data["key"] == "value"

    # Test update
    session.update_data({"key": "new_value"})
    assert session.data["key"] == "new_value"

    # Test expiration
    session.expire()
    assert session.is_expired()
```

### Testing Adapter Loading

```python
# test/test_adapters.py
def test_adapter_plugin_loading():
    """Test that adapters are discovered and loaded"""
    from ovos_plugin_manager.templates.gui import GuiAdapterModel

    adapters = GuiAdapterModel.get_all_plugins()
    assert len(adapters) > 0

    # Each adapter should have required methods
    for adapter in adapters:
        assert hasattr(adapter, 'initialize')
        assert hasattr(adapter, 'shutdown')
```

---

## Integration Tests

### Testing With Real MessageBus

```python
# test/test_integration.py
import pytest
from ovos_bus_client import MessageBusClient
from ovos_gui.manager import GUIManager

@pytest.mark.integration
class TestGUIIntegration:
    def test_skill_to_gui_flow(self, real_messagebus):
        """Test complete flow: skill sends data → GUI stores → adapter receives"""
        from ovos_utils.messagebus import Message

        # Start GUI manager
        gui = GUIManager(real_messagebus)
        gui.start()

        # Simulate skill sending weather
        message = Message(
            "gui.page.show",
            {
                "template": "SYSTEM_weather",
                "namespace": "skill-weather",
                "sessionId": "skill-weather:1",
                "sessionData": {
                    "current_temp": 22,
                    "condition": "Sunny"
                }
            }
        )

        real_messagebus.emit(message)

        # Wait for processing
        import time
        time.sleep(0.1)

        # Verify session was created
        assert gui.get_session_data("skill-weather") is not None

        gui.shutdown()
```

---

## Test Coverage

### Current Coverage

```bash
pytest test/ --cov=ovos_gui --cov-report=html
# Open htmlcov/index.html in browser
```

### Coverage Goals

- ✅ **Manager class**: 90%+ (critical path)
- ✅ **Session handling**: 85%+ (state management)
- ✅ **Bus handlers**: 80%+ (event routing)
- ✅ **Adapter loading**: 85%+ (plugin system)
- ⚠️ **Error paths**: 100% (catch all failures)

### Check Coverage Report

```bash
# Terminal report
pytest test/ --cov=ovos_gui --cov-report=term-missing

# Expected output:
# Name                    Stmts   Miss  Cover   Missing
# ─────────────────────────────────────────────────────
# ovos_gui/__init__.py       10      2    80%
# ovos_gui/manager.py       250     20    92%    123,456-460
# ovos_gui/session.py        95      5    95%    70-75
# ovos_gui/bus_handlers.py  180     15    91%    100-120
```

---

## Mocking & Fixtures

### Mock MessageBus

```python
# test/conftest.py
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_bus():
    """Create mock MessageBus"""
    bus = MagicMock()
    bus.emit = MagicMock()
    bus.on = MagicMock()
    return bus

@pytest.fixture
def mock_config():
    """Create mock configuration"""
    config = {
        "gui": {
            "idle_display_skill": "skill-ovos-homescreen.openvoiceos",
            "extension": "generic"
        },
        "gui_websocket": {
            "host": "0.0.0.0",
            "base_port": 18181
        }
    }
    return config
```

### Mock Adapter Plugins

```python
# test/test_adapters.py
@pytest.fixture
def mock_adapter():
    """Create mock adapter plugin"""
    from unittest.mock import MagicMock

    adapter = MagicMock()
    adapter.initialize = MagicMock()
    adapter.shutdown = MagicMock()
    adapter.emit_event = MagicMock()

    return adapter
```

---

## Testing MessageBus Protocol

### Verify Message Format

```python
# test/test_protocol.py
def test_gui_page_show_message_format():
    """Verify gui.page.show message format"""
    from ovos_utils.messagebus import Message

    message = Message(
        "gui.page.show",
        {
            "template": "SYSTEM_weather",
            "namespace": "skill-weather",
            "sessionId": "skill-weather:weather",
            "sessionData": {
                "current_temp": 22,
                "condition": "Cloudy",
                "location": "Berlin"
            }
        }
    )

    # Verify message structure
    assert message.msg_type == "gui.page.show"
    assert message.data["template"] == "SYSTEM_weather"
    assert message.data["sessionData"]["current_temp"] == 22
```

### Verify Event Sequence

```python
# test/test_event_flow.py
@pytest.mark.asyncio
async def test_complete_event_sequence():
    """Test complete event flow"""
    from ovos_gui.manager import GUIManager

    events_received = []

    def capture_event(message):
        events_received.append(message.msg_type)

    gui = GUIManager(mock_bus)

    # 1. Skill sends page.show
    gui._handle_page_show({
        "namespace": "skill-test",
        "sessionId": "test:1",
        "template": "SYSTEM_text",
        "sessionData": {"text": "Hello"}
    })

    # 2. Adapter should be notified
    assert "gui.page.show" in [e.msg_type for e in gui.messages_sent]

    # 3. Adapter sends interaction
    gui._handle_user_interaction({
        "namespace": "skill-test",
        "action": "button_clicked"
    })

    # 4. Event should be routed to skill
    assert any("skill.test" in str(e) for e in gui.messages_sent)
```

---

## Testing Adapter Interface

### Test Adapter Callbacks

```python
# test/test_adapter_callbacks.py
class TestAdapterCallbacks:
    def test_adapter_page_show_callback(self):
        """Test adapter receives page.show"""
        adapter_received = []

        # Mock adapter
        def on_page_show(namespace, template, data):
            adapter_received.append({
                "namespace": namespace,
                "template": template,
                "data": data
            })

        # Trigger event
        gui.page_show(
            namespace="skill-test",
            template="SYSTEM_text",
            data={"text": "Hello"}
        )

        # Verify callback was called
        assert len(adapter_received) == 1
        assert adapter_received[0]["template"] == "SYSTEM_text"
```

---

## Test-Driven Development

### When Adding a Feature

1. **Write test first** (should fail):
   ```python
   def test_new_feature():
       gui = GUIManager(mock_bus)
       result = gui.new_feature()
       assert result == expected_value
   ```

2. **Run test** (expect failure):
   ```bash
   pytest test/test_gui_manager.py::test_new_feature -v
   # FAILED - NotImplementedError
   ```

3. **Implement feature**:
   ```python
   # ovos_gui/manager.py
   def new_feature(self):
       return "feature implemented"
   ```

4. **Run test** (should pass):
   ```bash
   pytest test/test_gui_manager.py::test_new_feature -v
   # PASSED
   ```

5. **Run full suite** (ensure no regressions):
   ```bash
   pytest test/ --cov=ovos_gui
   ```

---

## Continuous Integration

### Before Pushing

```bash
# 1. Run all tests
pytest test/ -v

# 2. Check coverage
pytest test/ --cov=ovos_gui --cov-report=term-missing
# Should be 80%+ overall

# 3. Check code style
# (if pre-commit hooks are configured)
```

### GitHub Actions

Tests run automatically on:
- ✅ Every push to main/dev branches
- ✅ Every pull request
- ✅ Once per day (regression testing)

Check status:
```bash
gh run list --limit 10
gh run view <run-id>
```

---

## Common Test Issues

### Issue: "Cannot import ovos_gui"

**Solution**:
```bash
# Install in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH=/path/to/ovos-gui:$PYTHONPATH
pytest test/
```

### Issue: "MessageBus connection refused"

**Solution**: Use mocks for unit tests
```python
@pytest.fixture
def gui_with_mock_bus():
    from unittest.mock import MagicMock
    bus = MagicMock()
    return GUIManager(bus)
```

### Issue: "Test times out"

**Solution**: Use pytest-timeout
```bash
pip install pytest-timeout
pytest test/ --timeout=30
```

### Issue: "Flaky test passes sometimes"

**Solution**: Add explicit waits
```python
import asyncio

def test_async_behavior():
    async def run_test():
        gui = GUIManager(mock_bus)
        result = await gui.async_operation()
        assert result == expected

    asyncio.run(run_test())
```

---

## Best Practices

✅ **Do:**
- Write tests before implementing features
- Test both success and failure paths
- Use fixtures for common setup
- Test MessageBus message format and sequence
- Mock external dependencies (bus, adapters)
- Keep tests fast (< 1s each)
- Name tests clearly: `test_<component>_<scenario>`

❌ **Don't:**
- Test implementation details, test behavior
- Sleep in tests (use proper async/await)
- Create real files/directories in tests
- Test external services (use mocks)
- Skip tests without good reason
- Test multiple things in one test

---

## Resources

- **pytest documentation**: https://docs.pytest.org/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **Example tests**: See `test/` directory in this repo

---

## Next Steps

- Read [contributing.md](contributing.md) — Contribution guidelines
- Check [DEBUGGING.md](DEBUGGING.md) — Debugging techniques
- Review [adapter-development/bus-protocol.md](../adapter-development/bus-protocol.md) — Protocol to test against

---

**Happy testing!** ✅

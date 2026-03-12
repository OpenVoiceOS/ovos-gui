# Testing GUI Features — Unit & Integration Tests

Guide to testing skills with GUI components.

## Overview

Testing GUI features requires mocking the MessageBus and verifying that your skill sends the correct template data. Unlike QML/HTML rendering (which is the adapter's job), you test the skill's **contract** with the GUI system.

---

## Unit Testing with FakeBus

### Setup

```python
import unittest
from ovos_bus_client.message import Message
from ovos_utils.fakebus import FakeBus
from your_skill import MySkill

class TestMySkillGUI(unittest.TestCase):
    """Test GUI features."""

    def setUp(self):
        """Create skill with FakeBus."""
        self.bus = FakeBus()
        self.skill = MySkill(bus=self.bus)
        self.skill.initialize()

    def tearDown(self):
        """Cleanup."""
        self.skill.shutdown()
```

### Testing Template Display

```python
def test_show_weather_sends_correct_data(self):
    """Verify weather template data is sent."""
    # Call skill method
    self.skill.show_weather_from_intent(None)

    # Check that gui.request_page was emitted
    messages = self.bus.get_messages("gui.request_page")
    self.assertEqual(len(messages), 1)

    # Verify message data
    message = messages[0]
    data = message.data

    self.assertEqual(data["page"], "weather.qml")
    self.assertIn("namespace", data)
    self.assertIn("data", data)

    # Verify template fields
    template_data = data["data"]
    self.assertEqual(template_data["current_temp"], 22)
    self.assertEqual(template_data["condition"], "Cloudy")
    self.assertIn("location", template_data)
```

### Testing Event Handlers

```python
def test_handles_next_button_click(self):
    """Verify skill responds to button clicks."""
    # Setup
    self.skill.show_weather_from_intent(None)

    # Simulate user clicking "next" button
    user_message = Message(
        "gui.user_input",
        {
            "action": "next_day",
            "page": "weather"
        }
    )

    # Trigger the handler
    self.skill.on_weather_next(user_message)

    # Verify skill's response
    messages = self.bus.get_messages("gui.request_page")
    # Should have sent a new page (e.g., forecast)
    self.assertGreater(len(messages), 1)
```

---

## Full Example: Weather Skill Test

```python
import unittest
from unittest.mock import patch, MagicMock
from ovos_utils.fakebus import FakeBus
from ovos_bus_client.message import Message
from my_weather_skill import WeatherSkill

class TestWeatherSkillGUI(unittest.TestCase):
    """Test weather skill GUI integration."""

    def setUp(self):
        """Setup skill with mocked bus."""
        self.bus = FakeBus()
        self.skill = WeatherSkill(bus=self.bus)

        # Mock weather API
        self.weather_data = {
            "temp": 22,
            "min_temp": 18,
            "max_temp": 26,
            "condition": "Cloudy",
            "humidity": 65,
            "wind_speed": 15
        }

    def tearDown(self):
        """Cleanup."""
        self.skill.shutdown()

    def test_weather_intent_shows_gui(self):
        """Test that weather intent triggers GUI display."""
        with patch.object(
            self.skill,
            'get_weather',
            return_value=self.weather_data
        ):
            # Simulate intent
            message = Message("intent.weather", {})
            self.skill.handle_current_weather(message)

        # Verify GUI message sent
        messages = self.bus.get_messages("gui.request_page")
        self.assertEqual(len(messages), 1)

        # Verify it's a weather template
        gui_msg = messages[0]
        self.assertEqual(gui_msg.data["page"], "weather.qml")

    def test_weather_data_correct(self):
        """Test that template data is correct."""
        with patch.object(
            self.skill,
            'get_weather',
            return_value=self.weather_data
        ):
            message = Message("intent.weather", {})
            self.skill.handle_current_weather(message)

        gui_msg = self.bus.get_messages("gui.request_page")[0]
        data = gui_msg.data["data"]

        # Verify all expected fields
        self.assertEqual(data["current_temp"], 22)
        self.assertEqual(data["condition"], "Cloudy")
        self.assertEqual(data["min_temp"], 18)
        self.assertEqual(data["max_temp"], 26)
        self.assertEqual(data["humidity"], 65)
        self.assertEqual(data["wind_speed"], 15)

    def test_user_selects_next_day(self):
        """Test handling of next_day button click."""
        # First, show the forecast
        with patch.object(
            self.skill,
            'get_forecast',
            return_value={
                "Monday": {"high": 24, "low": 18},
                "Tuesday": {"high": 22, "low": 16}
            }
        ):
            message = Message("intent.forecast", {})
            self.skill.handle_forecast(message)

        # Clear messages
        self.bus.clear_messages()

        # User clicks "next day"
        user_input = Message(
            "gui.user_input",
            {"action": "next_day"}
        )
        self.skill.on_next_day_request(user_input)

        # Should update the display
        messages = self.bus.get_messages("gui.request_page")
        self.assertGreater(len(messages), 0)

    def test_fallback_when_no_adapter(self):
        """Test graceful degradation without display adapter."""
        # Simulate no adapter connected
        self.skill.gui.connected = False

        with patch.object(self.skill, 'speak_dialog') as mock_speak:
            message = Message("intent.weather", {})
            self.skill.handle_current_weather(message)

            # Should still speak, even without display
            mock_speak.assert_called()

    def test_session_context_updated(self):
        """Test that session context is properly managed."""
        with patch.object(
            self.skill,
            'get_weather',
            return_value=self.weather_data
        ):
            message = Message("intent.weather", {})
            self.skill.handle_current_weather(message)

        # Verify context is set (if skill sets context)
        # This would depend on your skill implementation
        # Example:
        # messages = self.bus.get_messages("gui.session.set")
        # self.assertGreater(len(messages), 0)


if __name__ == "__main__":
    unittest.main()
```

---

## Testing Message Handlers

### Test Event Handler Registration

```python
def test_event_handlers_registered(self):
    """Verify event handlers are registered on init."""
    # Skill.initialize() should register handlers
    self.skill.initialize()

    # Verify handlers exist (check skill's internal state)
    # This depends on how the skill framework tracks handlers
    # Example:
    # self.assertIn("music.next_button", self.skill._registered_handlers)
```

### Test Handler Invocation

```python
def test_next_button_handler_called(self):
    """Test that button click triggers correct handler."""
    with patch.object(self.skill, 'handle_next') as mock_handler:
        # Simulate button click
        message = Message("gui.user_input", {"action": "next"})

        # Trigger handler (how to do this depends on framework)
        self.skill.on_gui_event(message)

        # Verify handler was called
        mock_handler.assert_called_once()
```

---

## Integration Testing

### Using ovoscope (for Full E2E Tests)

For true end-to-end tests that include intent parsing and full skill lifecycle:

```python
from ovoscope import End2EndTest

class TestWeatherSkillE2E(End2EndTest):
    """End-to-end test with actual intent parsing."""

    skill_id = "skill-weather.openvoiceos"
    utterance = "what's the weather"

    def test_weather_intent_flow(self):
        """Test complete flow from utterance to GUI."""
        results = self.execute()

        # Verify intent was recognized
        self.assertMessageType(
            results,
            "recognizer_loop:audio_output_start",
            "Intent should be recognized"
        )

        # Verify GUI message was sent
        gui_messages = [
            m for m in results.messages
            if m["type"] == "gui.request_page"
        ]
        self.assertGreater(
            len(gui_messages),
            0,
            "GUI message should be sent"
        )

        # Verify GUI data
        gui_data = gui_messages[0]["data"]["data"]
        self.assertIn("current_temp", gui_data)
        self.assertIn("condition", gui_data)


if __name__ == "__main__":
    test = TestWeatherSkillE2E()
    test.test_weather_intent_flow()
```

---

## Testing Best Practices

### 1. Mock External APIs

```python
@patch('requests.get')
def test_fetches_weather_data(self, mock_get):
    """Test skill correctly fetches and displays weather."""
    mock_get.return_value.json.return_value = {
        "temp": 22,
        "condition": "Cloudy"
    }

    self.skill.handle_weather(Message("test", {}))

    # Verify API was called
    mock_get.assert_called_once()
```

### 2. Test Data Validation

```python
def test_invalid_temperature_handled(self):
    """Test skill handles invalid temperature gracefully."""
    bad_data = {
        "current_temp": "invalid",  # Should be a number
        "condition": "Cloudy"
    }

    # Skill should either reject or convert
    message = Message("intent.weather", bad_data)
    self.skill.handle_current_weather(message)

    # Verify graceful handling (no crash)
    # and appropriate user feedback
```

### 3. Test Error Conditions

```python
@patch.object(MySkill, 'get_weather')
def test_api_failure_handled(self, mock_api):
    """Test skill handles API failures gracefully."""
    mock_api.side_effect = ConnectionError("API down")

    message = Message("intent.weather", {})
    self.skill.handle_current_weather(message)

    # Skill should speak an error message
    # (or show error GUI)
```

### 4. Test Async Operations

```python
def test_async_gui_update(self):
    """Test async GUI updates."""
    from threading import Event

    update_complete = Event()

    def on_gui_update(msg):
        update_complete.set()

    self.bus.on("gui.request_page", on_gui_update)

    # Trigger async operation
    self.skill.handle_async_weather()

    # Wait for completion
    self.assertTrue(
        update_complete.wait(timeout=5),
        "GUI update should complete"
    )
```

---

## Checking Message Bus Communication

### Print All Messages

```python
def test_debug_all_messages(self):
    """Debug: print all bus messages."""
    self.skill.handle_current_weather(Message("test", {}))

    # Print all messages sent
    for msg_type, messages in self.bus.messages.items():
        print(f"{msg_type}: {len(messages)} messages")
        for msg in messages:
            print(f"  Data: {msg.data}")
```

### Check Specific Message Types

```python
def test_message_types_sent(self):
    """Verify correct message types are sent."""
    self.skill.handle_current_weather(Message("test", {}))

    # Check what messages were sent
    self.assertIn("gui.request_page", self.bus.messages)

    # Optionally check for speech
    self.assertIn("speak", self.bus.messages)
```

---

## Common Pitfalls

### ❌ Don't Test the Adapter
You shouldn't test that QML renders correctly — that's the adapter's job.

```python
# ❌ Bad: Testing adapter behavior
def test_image_displays_correctly(self):
    """This is NOT your responsibility."""
    self.skill.show_image("photo.jpg")
    # Can't test rendering without running the adapter
```

### ✅ Do Test Your Data Contract
Test that your skill sends the correct template data.

```python
# ✅ Good: Testing data contract
def test_image_data_sent(self):
    """Verify image path is sent correctly."""
    self.skill.show_image("photo.jpg")

    messages = self.bus.get_messages("gui.request_page")
    data = messages[0].data["data"]
    self.assertEqual(data["image"], "photo.jpg")
```

### ❌ Don't Over-Mock
Avoid mocking the entire skill framework.

```python
# ❌ Bad: Too much mocking
@patch('ovos_workshop.skills.OVOSSkill')
@patch('ovos_bus_client.MessageBusClient')
def test_something(self, mock_bus, mock_skill):
    # Now you're testing mocks, not your code
    pass
```

### ✅ Use FakeBus
Let the real framework run; only mock external dependencies.

```python
# ✅ Good: Mock only external APIs
def setUp(self):
    self.bus = FakeBus()  # Real bus, controlled
    self.skill = MySkill(bus=self.bus)

@patch('requests.get')  # Only mock external API
def test_weather(self, mock_api):
    pass
```

---

## Running Tests

```bash
# Run all GUI tests
python -m pytest test/ -v -k "gui"

# Run with coverage
python -m pytest test/ --cov=your_skill

# Run specific test
python -m pytest test/test_gui.py::TestMySkillGUI::test_show_weather
```

---

## See Also

- **[Skill GUI Development](skill-gui-development.md)** — Template methods reference
- **[Skill Examples](skill-examples.md)** — Real working examples
- **[Core Concepts](concepts.md)** — MessageBus and namespace details
- **[ovoscope Documentation](../../ovoscope/docs/index.md)** — E2E testing framework

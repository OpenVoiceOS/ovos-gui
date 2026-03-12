# Quick Start — OVOS GUI in 5 Minutes

Get your first GUI up and running in under 5 minutes.

## Step 1: Install

Assuming you have OVOS installed:

```bash
# Install the GUI service
pip install ovos-gui

# Install a display adapter (Qt5 for desktop, or web for any device)
pip install ovos-legacy-mycroft-gui-plugin      # Qt5 desktop
# OR
pip install ovos-gui-plugin-web                 # Browser-based
```

## Step 2: Create a Simple Skill

Create a new skill file `my_skill.py`:

```python
from ovos_workshop.skills import OVOSSkill
from ovos_workshop.decorators import intent_handler
from ovos_workshop.intents import IntentBuilder

class WeatherSkill(OVOSSkill):
    """A simple weather skill with GUI display."""

    @intent_handler(IntentBuilder("WeatherIntent").require("weather"))
    def handle_weather_intent(self, message):
        # Get current weather (mock data for this example)
        current_temp = 22
        condition = "Partly Cloudy"
        location = "Berlin"
        min_temp = 18
        max_temp = 26

        # Show the weather GUI
        self.gui.show_weather(
            current_temp=current_temp,
            min_temp=min_temp,
            max_temp=max_temp,
            condition=condition,
            location=location,
            icon="cloud.png"
        )

        # Speak the weather
        self.speak_dialog(
            "weather_template",
            data={
                "temp": current_temp,
                "condition": condition,
                "location": location
            }
        )

    def create_settings_meta_file(self):
        """Define skill metadata."""
        return {
            "name": "Weather Skill",
            "description": "Display weather on your screen",
            "author": "You",
            "license": "Apache-2.0"
        }


def create_skill():
    return WeatherSkill()
```

## Step 3: Install the Skill

```bash
# Navigate to your skill directory
cd my-weather-skill

# Install it in development mode
pip install -e .
```

## Step 4: Start OVOS

In one terminal:

```bash
# Start the GUI service
ovos-gui-service
```

In another terminal:

```bash
# Start the core (if not already running)
ovos-core
```

In a third terminal:

```bash
# Start the display adapter
ovos-legacy-mycroft-gui-plugin  # For Qt5
# OR for web-based:
ovos-gui-plugin-web
```

## Step 5: Trigger Your Skill

```bash
# In the OVOS shell or via voice
weather
```

Your weather GUI should now appear on screen!

---

## What Just Happened?

1. **You wrote a skill** that calls `self.gui.show_weather()`
2. **The GUI service** created a namespace and page with your template data
3. **The display adapter** received the data and rendered it
4. **Users see the weather** without you writing any QML or HTML

That's the beauty of the template API: **one skill, many display adapters**.

---

## Next Steps

- **Add more templates**: Read [Skill GUI Development](skill-gui-development.md) for all 21 available templates
- **See real examples**: Check [Skill Examples](skill-examples.md)
- **Handle user input**: Learn about buttons and interactions in [Templates](templates.md)
- **Custom adapter**: Interested in building your own GUI? See [Adapter Plugin System](adapter-plugins.md)

## Troubleshooting

**"ModuleNotFoundError: No module named 'ovos_gui'"**
- Install ovos-gui: `pip install ovos-gui`

**"No display adapter found"**
- Install a display adapter: `pip install ovos-legacy-mycroft-gui-plugin`

**"GUI doesn't appear"**
- Check logs: `tail -f ~/.local/share/ovos/logs/ovos-gui-service.log`
- Ensure MessageBus is running: `ovos-messagebus` (default port 8181)
- Verify adapter is running in separate terminal

**Still stuck?**
- See [Monitoring & Debugging](monitoring.md) for troubleshooting
- Check [Common Issues](#) in the FAQ

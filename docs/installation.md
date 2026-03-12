# Installation & Setup — OVOS GUI

Complete guide to installing `ovos-gui` and configuring display adapters.

## Prerequisites

- **Python**: 3.10 or higher
- **OVOS Core**: Installed and running
- **MessageBus**: Running on localhost:8181 (default)

## Installation

### 1. Install the GUI Service

```bash
# From PyPI (stable)
pip install ovos-gui

# From development branch
git clone https://github.com/OpenVoiceOS/ovos-gui.git
cd ovos-gui
pip install -e .
```

**Verify installation:**
```bash
python -c "import ovos_gui; print(ovos_gui.__version__)"
```

### 2. Install a Display Adapter

Choose one or more display adapters based on your use case:

#### Qt5 Desktop (Recommended for Linux desktop)

```bash
pip install ovos-legacy-mycroft-gui-plugin
```

**Requirements**: Qt5 libraries
```bash
# Ubuntu/Debian
sudo apt-get install qt5-qmake qt5-default libqt5gui5

# Fedora
sudo dnf install qt5-qtbase qt5-qtbase-gui

# macOS
brew install qt5
```

#### Web-Based GUI (Works anywhere)

```bash
pip install ovos-gui-plugin-web
```

**No additional dependencies** — uses HTML/CSS/JavaScript.

#### Headless (Terminal-only debugging)

```bash
# Built-in; no separate package needed
ovos-gui-debug-tui
```

### 3. Configure MycroftAI

Edit `~/.config/mycroft/mycroft.conf`:

```json
{
  "gui": {
    "extensions": {
      "debug": false
    },
    "idle_display_skill": "skill-ovos-homescreen",
    "idle_display_timeout": 300
  }
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `extensions.debug` | bool | `false` | Enable GUI debugging mode |
| `idle_display_skill` | str | (none) | Skill to show when idle |
| `idle_display_timeout` | int | 300 | Idle display timeout in seconds |

### 4. Run the GUI Service

Start the GUI service:

```bash
# As a daemon
ovos-gui-service &

# Or in the foreground (for debugging)
ovos-gui-service
```

**Logs location**: `~/.local/share/ovos/logs/ovos-gui-service.log`

### 5. Run a Display Adapter

In another terminal:

```bash
# Qt5 Desktop
ovos-legacy-mycroft-gui-plugin

# Web (browser-based)
ovos-gui-plugin-web --host 0.0.0.0 --port 5000
```

Then open your browser to `http://localhost:5000`

---

## Verifying Installation

### Check that services are running

```bash
ps aux | grep -E "ovos-gui-service|mycroft|messagebus"
```

You should see:
- `ovos-messagebus` (or similar)
- `ovos-gui-service` (or just `gui-service`)
- `ovos-legacy-mycroft-gui-plugin` or `ovos-gui-plugin-web`

### Check MessageBus connectivity

```bash
# Install debugging tool
pip install ovoscope

# Connect to MessageBus
python -c "
from ovos_bus_client import MessageBusClient
bus = MessageBusClient()
bus.connect()
print('Connected to MessageBus on', bus.config.get('host'))
bus.close()
"
```

### Check GUI service health

```bash
# View recent logs
tail -n 20 ~/.local/share/ovos/logs/ovos-gui-service.log

# Look for:
# - "GUI Service started"
# - "Connected to messagebus"
# - "Loaded adapters: [...]"
```

---

## Advanced Configuration

### Multiple Display Adapters

You can run multiple adapters simultaneously. Each will receive events independently:

```bash
# Terminal 1: Qt5 desktop
ovos-legacy-mycroft-gui-plugin &

# Terminal 2: Web browser
ovos-gui-plugin-web --port 5000 &

# Terminal 3: Headless debugging
ovos-gui-debug-tui &
```

Users can interact with any adapter, and the skill receives input from whichever one they use.

### Custom Namespace Configuration

Override the default namespace display:

```json
{
  "gui": {
    "routes": {
      "skill-weather": {
        "adapter": "qt5"
      },
      "skill-music": {
        "adapter": "web"
      }
    }
  }
}
```

### Timeout & Idle Display

```json
{
  "gui": {
    "idle_display_skill": "skill-ovos-homescreen",
    "idle_display_timeout": 300,
    "page_keep_alive": true
  }
}
```

| Setting | Default | Description |
|---------|---------|-------------|
| `idle_display_skill` | (none) | Skill to show when no skill is active |
| `idle_display_timeout` | 300s | Time before returning to idle |
| `page_keep_alive` | false | Keep last page alive after timeout |

---

## Troubleshooting

### GUI Service Won't Start

**Error**: `ModuleNotFoundError: No module named 'ovos_gui'`
```bash
pip install ovos-gui
```

**Error**: `Address already in use` (port 8181)
```bash
# Another service is using the port. Check:
lsof -i :8181
# Kill the process:
kill -9 <PID>
```

### Adapter Won't Connect

**Error**: `ConnectionRefused to localhost:8181`
- Ensure `ovos-messagebus` is running
- Check firewall: `sudo ufw allow 8181/tcp`
- Check OVOS config: `cat ~/.config/mycroft/mycroft.conf | grep -A5 "messagebus"`

**Error**: `No GUI adapters loaded`
```bash
# Install an adapter
pip install ovos-legacy-mycroft-gui-plugin
```

### No Display Appears

1. **Check logs**:
   ```bash
   tail -f ~/.local/share/ovos/logs/ovos-gui-service.log
   ```

2. **Verify adapter is running**:
   ```bash
   ps aux | grep gui
   ```

3. **Check MessageBus connectivity**:
   ```bash
   netstat -an | grep 8181
   ```

4. **Trigger a test skill**:
   ```bash
   # From OVOS CLI
   > weather
   ```

5. **Enable debug mode** in `mycroft.conf`:
   ```json
   {
     "gui": {
       "extensions": {
         "debug": true
       }
     }
   }
   ```

### Qt5 Display Issues

**Problem**: Qt5 libraries not found
```bash
# Ubuntu/Debian
sudo apt-get install libqt5gui5 libqt5widgets5

# Check installation
pkg-config --cflags Qt5Gui
```

**Problem**: Rendering is slow
- See [Performance Optimization](performance.md)

---

## Next Steps

- **Start building skills**: [Skill GUI Development](skill-gui-development.md)
- **See examples**: [Skill Examples](skill-examples.md)
- **Build custom adapter**: [Adapter Plugin System](adapter-plugins.md)
- **Monitor production**: [Monitoring & Debugging](monitoring.md)

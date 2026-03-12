# Monitoring & Debugging — Logging and Troubleshooting

Guide to debugging GUI issues and monitoring production deployments.

## Overview

When GUI features aren't working, start with logs. The OVOS GUI system logs all significant events and errors.

---

## Log Locations

### GUI Service Logs

```bash
# Default location
~/.local/share/ovos/logs/ovos-gui-service.log

# Or check all logs
ls -la ~/.local/share/ovos/logs/
```

### Reading Logs

```bash
# View last 20 lines
tail -n 20 ~/.local/share/ovos/logs/ovos-gui-service.log

# Follow live logs
tail -f ~/.local/share/ovos/logs/ovos-gui-service.log

# Search for errors
grep -i error ~/.local/share/ovos/logs/ovos-gui-service.log

# Search with context
grep -B5 -A5 "Error" ~/.local/share/ovos/logs/ovos-gui-service.log
```

---

## Debug Mode

### Enable Debug Logging

Edit `~/.config/mycroft/mycroft.conf`:

```json
{
  "gui": {
    "extensions": {
      "debug": true
    },
    "debug_log_level": "DEBUG"
  },
  "log_level": "DEBUG"
}
```

Then restart:

```bash
# Stop GUI service
killall ovos-gui-service

# Restart with debug enabled
ovos-gui-service
```

### Debug Output

With debug mode enabled, you'll see:

```
[2026-03-12 10:30:45] DEBUG - Creating namespace: skill-weather.openvoiceos
[2026-03-12 10:30:45] DEBUG - Template: weather
[2026-03-12 10:30:45] DEBUG - Data keys: ['current_temp', 'condition', 'location']
[2026-03-12 10:30:46] DEBUG - Adapter weather.openvoiceos received: gui.page_show
[2026-03-12 10:30:46] DEBUG - Rendering weather template
```

---

## Common Issues and Solutions

### Issue: GUI Doesn't Appear

**Symptoms**: You call `self.gui.show_weather()` but nothing appears.

**Debug steps**:

1. **Check service is running**:
   ```bash
   ps aux | grep ovos-gui
   ```

2. **Check MessageBus is running**:
   ```bash
   netstat -an | grep 8181
   # Should show listening on 8181
   ```

3. **Check adapter is running**:
   ```bash
   ps aux | grep -E "gui-plugin|legacy-mycroft"
   ```

4. **Enable debug and check logs**:
   ```bash
   tail -f ~/.local/share/ovos/logs/ovos-gui-service.log
   ```

5. **Test with debug TUI**:
   ```bash
   # In another terminal
   ovos-gui-debug-tui
   ```
   This shows a text-based display of what the GUI would show.

### Issue: Event Handler Not Firing

**Symptoms**: User clicks button but handler isn't called.

**Debug**:

1. **Verify handler is registered**:
   ```python
   def initialize(self):
       self.log.info("Registering weather.next_button handler")
       self.gui.register_handler(
           "weather.next_button",
           self.on_next_button
       )
       self.log.info("Handler registered")
   ```

2. **Check event name matches**:
   - Adapter sends: `weather.next_button`
   - Handler name: `weather.next_button`
   - These must match exactly (case-sensitive)

3. **Test event reception**:
   ```python
   # Register a catch-all handler
   self.gui.register_handler("*", self.on_any_gui_event)

   def on_any_gui_event(self, message):
       self.log.info(f"Received GUI event: {message.type}")
       self.log.info(f"Data: {message.data}")
   ```

4. **Check logs for event**:
   ```bash
   tail -f ~/.local/share/ovos/logs/ovos-gui-service.log | grep "user_input\|session_update"
   ```

### Issue: Slow GUI Updates

**Symptoms**: Page changes take several seconds to appear.

**Causes and solutions**:

1. **Large payload** — Template data > 1 MB
   ```python
   # ❌ Bad
   self.gui.show_list(items=database.get_all_users())  # Might be 10000s items

   # ✅ Good
   self.gui.show_list(items=database.get_users(limit=20))  # Paginated
   ```

2. **Network latency** — MessageBus is slow
   ```bash
   # Check MessageBus response time
   netstat -s | grep tcp
   # High retransmits or timeouts indicate network issues
   ```

3. **Adapter is slow** — Rendering takes time
   - Check adapter logs: `~/.local/share/ovos/logs/`
   - For Qt5: Check CPU/memory usage
   - See [Performance Optimization](performance.md)

### Issue: Memory Leak

**Symptoms**: GUI service memory usage grows over time.

**Debug**:

1. **Check process memory**:
   ```bash
   watch -n 1 'ps aux | grep ovos-gui'
   # Monitor the RSS column
   ```

2. **Check for unclosed event handlers**:
   ```python
   # Make sure to remove handlers
   def shutdown(self):
       self.gui.remove_handler("weather.next_button")
   ```

3. **Check for circular references**:
   - Event handlers should not hold references back to skill
   - Use weakref if needed

### Issue: MessageBus Connection Failed

**Symptoms**: Logs show "ConnectionRefused" or "Unable to connect to MessageBus"

**Solutions**:

1. **Start MessageBus**:
   ```bash
   ovos-messagebus
   ```

2. **Check port is available**:
   ```bash
   lsof -i :8181
   # If something is using it:
   kill -9 <PID>
   ```

3. **Check configuration**:
   ```bash
   cat ~/.config/mycroft/mycroft.conf | grep messagebus
   # Should show:
   # "messagebus": {
   #   "host": "localhost",
   #   "port": 8181
   # }
   ```

4. **Check firewall**:
   ```bash
   # If remote access needed
   sudo ufw allow 8181/tcp
   ```

---

## Monitoring in Production

### Key Metrics

Monitor these to detect issues early:

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| GUI service uptime | >99% | <99% | Service down |
| Page show latency | <500ms | 500-2000ms | >2000ms |
| Memory usage | <100MB | 100-300MB | >300MB |
| Event handler count | 1-10 | 11-50 | >50 (possible leak) |
| MessageBus lag | <100ms | 100-500ms | >500ms |

### Log Monitoring

Set up automated log parsing:

```bash
#!/bin/bash
# Check for errors in last hour
grep -i "error\|exception\|critical" \
  ~/.local/share/ovos/logs/ovos-gui-service.log \
  | tail -n 20
```

### SystemD Service

For production, run as a systemd service:

```ini
# /etc/systemd/system/ovos-gui.service
[Unit]
Description=OVOS GUI Service
Requires=ovos-messagebus.service
After=ovos-messagebus.service

[Service]
Type=simple
ExecStart=/usr/local/bin/ovos-gui-service
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable ovos-gui.service
sudo systemctl start ovos-gui.service
sudo systemctl status ovos-gui.service
```

View logs:

```bash
sudo journalctl -u ovos-gui.service -f
```

---

## Logging from Skills

### Enable Logging in Your Skill

```python
from ovos_utils.log import LOG

class MySkill(OVOSSkill):
    def handle_intent(self, message):
        LOG.info(f"Handling intent: {message.intent_type}")
        LOG.debug(f"Message data: {message.data}")

        try:
            self.gui.show_weather(...)
        except Exception as e:
            LOG.exception(f"Failed to show weather: {e}")
```

### Log Levels

| Level | Use For | Example |
|-------|---------|---------|
| DEBUG | Detailed tracing | Variable values, function calls |
| INFO | Important events | "Handling weather intent", "Showing page" |
| WARNING | Potential issues | Missing data, unusual conditions |
| ERROR | Recoverable errors | API failure, invalid input |
| CRITICAL | Unrecoverable errors | Service crash, data corruption |

### Enable Skill Logging

In `mycroft.conf`:

```json
{
  "log_level": "DEBUG",
  "skills": {
    "skill-weather": {
      "log_level": "DEBUG"
    }
  }
}
```

---

## Network Debugging

### Check MessageBus Connectivity

```python
# test_connection.py
from ovos_bus_client import MessageBusClient

client = MessageBusClient()
client.connect()

# Send a test message
client.emit_message(
    Message("test.message", {"data": "hello"})
)

print("✓ MessageBus connection OK")
client.close()
```

Run it:

```bash
python test_connection.py
```

### Monitor Network Traffic

```bash
# Monitor all messages on the bus (requires tcpdump)
sudo tcpdump -i lo port 8181 -A

# Or use wireshark for GUI analysis
wireshark
```

---

## Profiling Performance

### Profile GUI Service

```python
# profile_gui.py
import cProfile
import pstats
from ovos_gui.service import GUIService

prof = cProfile.Profile()
prof.enable()

# Run GUI service operations
service = GUIService()
# ... do operations ...

prof.disable()
stats = pstats.Stats(prof)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Profile a script
python -m memory_profiler my_script.py
```

---

## Log Analysis

### Extract Relevant Errors

```bash
# Find all errors in the last hour
grep "$(date --date='1 hour ago' +%Y-%m-%d)" \
  ~/.local/share/ovos/logs/ovos-gui-service.log | grep -i error
```

### Timeline Analysis

```bash
# Show events in order with timestamps
tail -n 100 ~/.local/share/ovos/logs/ovos-gui-service.log | \
  grep "show_page\|page_show\|user_input" | \
  cut -d']' -f1,3-
```

---

## Troubleshooting Checklist

Use this checklist when GUI isn't working:

- [ ] GUI service is running: `ps aux | grep ovos-gui`
- [ ] MessageBus is running: `ps aux | grep messagebus`
- [ ] Adapter is running: `ps aux | grep gui-plugin`
- [ ] MessageBus port is open: `netstat -an | grep 8181`
- [ ] No errors in GUI logs: `grep -i error ~/.local/share/ovos/logs/ovos-gui-service.log`
- [ ] Event handlers are registered: `grep "register_handler" skill logs`
- [ ] Template data is valid: Check against `docs/templates.md`
- [ ] Adapter supports the template: Check adapter docs
- [ ] Network connectivity is OK: Ping MessageBus
- [ ] Configuration is correct: Check `mycroft.conf`

---

## Getting Help

If you're still stuck:

1. **Enable debug mode** and capture logs
2. **Isolate the problem**: Is it the skill? Adapter? Service?
3. **Search existing issues**: [GitHub Issues](https://github.com/OpenVoiceOS/ovos-gui/issues)
4. **Report with logs**: Include `ovos-gui-service.log` and skill logs
5. **Ask in community**: [Forums](https://openvoiceos.com/forum) or [Discord](https://discord.gg/OpenVoiceOS)

---

## See Also

- **[Performance Optimization](performance.md)** — Tuning for speed
- **[Testing GUI](testing-gui.md)** — Unit testing to catch issues early
- **[Skill GUI Development](skill-gui-development.md)** — Best practices for skills

# GUI Media Player Bundle Pattern

**Date:** 2026-03-13  
**Status:** Draft  
**Related:** `adapter-development/adapter-plugins.md`, `ovos-media/docs/architecture.md`

---

## Problem Statement

GUI clients (Qt, web browser, terminal) can render audio, video, and web content natively on the client device. However, `ovos-media` has no mechanism to leverage these rendering capabilities because:

1. Media backends are separate plugins discovered by `ovos-plugin-manager`
2. GUI adapters handle UI rendering via `SYSTEM_*` templates
3. No connection exists between the two — each operates independently

Currently, if you want media playback on a GUI client, you must run a separate media backend (VLC, MPV, etc.) that isnt a unified UI and often fails for video/web content.

---

## Proposed Solution: Adapter + Backend Bundle

Bundle a **media backend plugin** with each GUI adapter package. The backend registers with `ovos-media` as a standard audio/video/web backend. Internally, it communicates with the GUI adapter to render media on the client.

```
ovos-legacy-mycroft-gui-plugin (package)
├── opm.gui            → GUI Adapter (existing) — renders SYSTEM_* templates
└── opm.plugin.audio   → Media Backend Plugin (new) — handles playback, talks to adapter
```

### Why This Works

- **Transparent to `ovos-media`**: The backend is a regular OCP backend — no special handling needed
- **Adapter knows client capabilities**: By design, the adapter knows what its clients can render (Qt can do video, terminal can't, etc.)
- **No capability negotiation**: Each adapter ships a backend matching exactly what its clients support
- **Uses existing communication**: The GUI WebSocket protocol already exists between adapter and client

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           ovos-media                                │
│                                                                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│   │ AudioService │  │ VideoService │  │  WebService  │             │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│          │                 │                 │                      │
│          ▼                 ▼                 ▼                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│   │ QtAudioBackend│ │ QtVideoBackend│ │ QtWebBackend  │  ← BUNDLED  │
│   │ (plugin)     │  │ (plugin)     │  │ (plugin)      │             │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│          │                 │                 │                      │
└──────────│─────────────────│─────────────────│──────────────────────┘
           │                 │                 │
           ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       ovos-gui (service)                            │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────┐       │
│   │              QtGUIAdapter (opm.gui)                      │       │
│   │  - dispatch_template("SYSTEM_weather", ...)              │       │
│   │  - dispatch_template("SYSTEM_media_player", ...)         │       │
│   └──────────────────────────────────────────────────────────┘       │
│                              ▲                                       │
└──────────────────────────────│──────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │   Qt Client      │
                    │  (QML/JS runtime)│
                    │  - VideoPlayer   │
                    │  - WebView      │
                    └──────────────────┘
```

### Message Flow: Play Video

1. Skill/OCP requests: `ovos.common_play.play` with video URI
2. `VideoService` selects `QtVideoBackend` (bundled with Qt adapter)
3. Backend calls `load_track(uri)` → emits `ovos.common_play.media.state` → `LOADED_MEDIA`
4. Backend's `play()` → sends media URL to GUI client via WebSocket
5. Qt client renders in native `VideoItem` QML component

---

## Implementation

### 1. Entry Points

Each bundled backend registers under the appropriate OPM entry point:

```toml
# pyproject.toml
[project.entry-points."opm.plugin.audio"]
qt-gui-audio = "ovos_qt_gui_plugin.media:QtGuiAudioBackend"

[project.entry-points."opm.plugin.video"]  
qt-gui-video = "ovos_qt_gui_plugin.media:QtGuiVideoBackend"

[project.entry-points."opm.plugin.web"]
qt-gui-web = "ovos_qt_gui_plugin.media:QtGuiWebBackend"
```

### 2. Backend Implementation

```python
# qt_gui_plugin/media.py
from ovos_plugin_manager.templates.media import MediaBackend
from ovos_bus_client.message import Message
from ovos_utils.ocp import MediaState, PlayerState


class QtGuiVideoBackend(MediaBackend):
    """Video backend that renders on Qt GUI client via adapter."""

    def __init__(self, config=None, bus=None):
        super().__init__(config, bus)
        self.name = "qt-gui-video"
        self.gui_message_target = None  # Set by adapter

    def supported_uris(self):
        # Advertise all common video URIs
        return ["http", "https", "file", "rtsp", "rtmp"]

    def load_track(self, uri: str, metadata: dict = None):
        self._now_playing = uri
        self.meta.update(metadata or {})
        # Emit OCP state — this is required for OCP to recognize playback
        self.bus.emit(Message("ovos.common_play.media.state",
                              {"state": MediaState.LOADED_MEDIA}))

    def play(self):
        # Forward to GUI client via adapter's internal channel
        self.bus.emit(Message("ovos.gui.player.play", data={
            "uri": self._now_playing,
            "type": "video",
            "meta": self.meta
        }))
        self.bus.emit(Message("ovos.common_play.player.state",
                              {"state": PlayerState.PLAYING}))

    def pause(self):
        self.bus.emit(Message("ovos.gui.player.pause", data={"type": "video"}))

    def stop(self):
        self.bus.emit(Message("ovos.gui.player.stop", data={"type": "video"}))

    def get_track_position(self):
        # Query client for position via synchronous message
        # Implementation depends on adapter's message protocol
        return 0

    def seek_forward(self, milliseconds: int = 5000):
        self.bus.emit(Message("ovos.gui.player.seek", data={
            "type": "video",
            "delta": milliseconds
        }))

    def seek_backward(self, milliseconds: int = 5000):
        self.seek_forward(-milliseconds)
```

### 3. Adapter Internal Communication

The backend and adapter share a message bus. Use internal messages (not exposed to clients):

```python
# In QtGUIAdapter
def __init__(self, config, bus):
    super().__init__(config, bus)
    # Listen for media control from bundled backend
    bus.on("ovos.gui.player.play", self._handle_player_play)
    bus.on("ovos.gui.player.pause", self._handle_player_pause)
    bus.on("ovos.gui.player.stop", self._handle_player_stop)
    bus.on("ovos.gui.player.seek", self._handle_player_seek)

def _handle_player_play(self, message):
    # Forward to connected Qt client via WebSocket
    self.send_to_client(message.data, event="player.play")

def _handle_player_pause(self, message):
    self.send_to_client(message.data, event="player.pause")
```

### 4. Qt Client Protocol Extension

Extend the Qt GUI protocol to support media events:

```javascript
// From server: media control messages
{
    "type": "gui.player.play",
    "data": {
        "uri": "https://example.com/video.mp4",
        "type": "video",
        "meta": { ... }
    }
}
```

---

## Configuration

```json
{
    "media": {
        "video_players": {
            "qt-gui-video": {
                "module": "ovos_qt_gui_plugin.media",
                "aliases": ["Qt GUI", "Qt Client"],
                "active": true
            }
        }
    }
}
```

---

## Task List

### Phase 1: Protocol Foundation
- [x] Add player event messages to Qt protocol: `gui.player.play`, `gui.player.pause`, `gui.player.stop`, `gui.player.seek`
- [x] Document internal adapter-backend message contract

### Phase 2: Qt GUI Implementation
- [x] Create `ovos_qt_gui_plugin/media.py` with `QtGuiAudioBackend`, `QtGuiVideoBackend`, `QtGuiWebBackend`
- [x] Register entry points in `pyproject.toml`
- [x] Implement adapter message handlers (`_handle_player_play`, etc.)
- [x] Implement Qt client media rendering (QML `VideoItem`, `WebEngineView`)

## References

- [GUI Adapter Plugins](adapter-development/adapter-plugins.md) — existing adapter documentation
- [Qt GUI Protocol](../protocol/qt-gui-protocol.md) — client connection protocol
- [ovos-media architecture](../../ovos-media/docs/01-history-and-architecture.md) — media service design
- [Media Backend Templates](https://github.com/OpenVoiceOS/ovos-plugin-manager/blob/dev/ovos_plugin_manager/templates/media.py) — `MediaBackend` base class

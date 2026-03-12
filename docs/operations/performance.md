# Performance Optimization — Tuning for Speed

Guide to optimizing GUI performance for embedded devices and high-latency networks.

## Overview

OVOS GUI is designed to work on embedded devices with limited resources. However, certain patterns can significantly impact performance. This guide shows how to optimize skills and adapters.

---

## Measuring Performance

### Key Metrics

| Metric | Target | Acceptable | Poor |
|--------|--------|-----------|------|
| Page show latency | <300ms | <500ms | >1000ms |
| Page render time | <200ms | <500ms | >1000ms |
| Memory per skill | <50MB | <100MB | >200MB |
| Payload size | <100KB | <500KB | >1MB |
| Event handler count | <5 | <20 | >50 |

### Measuring Latency

```python
import time

class MySkill(OVOSSkill):
    def handle_weather_intent(self, message):
        """Measure time from intent to GUI display."""
        start = time.time()

        # Your code here
        self.gui.show_weather(...)

        elapsed = (time.time() - start) * 1000  # Convert to ms
        self.log.info(f"Page show latency: {elapsed:.0f}ms")
```

---

## Skill Optimization

### 1. Minimize Payload Size

Large JSON payloads are slow to serialize and transmit.

```python
# ❌ Bad: Sending unnecessary data
def handle_news(self, message):
    articles = self.fetch_news()  # Might be 10000s of items

    self.gui.show_generic(
        data={
            "articles": articles,  # Huge payload!
            "metadata": {...}
        }
    )

# ✅ Good: Send only what's visible
def handle_news(self, message):
    articles = self.fetch_news(limit=10)  # First 10 articles

    self.gui.show_generic(
        data={
            "articles": articles,  # Smaller payload
            "total_available": len(self.all_articles),
            "page": 1
        }
    )
```

### 2. Cache Remote Data

Don't re-fetch data for every page load.

```python
class WeatherSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.weather_cache = {}
        self.cache_timeout = 300  # 5 minutes

    def get_weather(self, location, use_cache=True):
        """Fetch weather with caching."""
        if use_cache and location in self.weather_cache:
            cached_data, cached_time = self.weather_cache[location]
            age = time.time() - cached_time

            if age < self.cache_timeout:
                self.log.debug("Using cached weather")
                return cached_data

        # Fetch fresh data
        data = self.fetch_weather_from_api(location)
        self.weather_cache[location] = (data, time.time())
        return data

    def handle_weather(self, message):
        """Show weather."""
        location = message.data.get("location", "Berlin")
        weather = self.get_weather(location)  # Fast if cached
        self.gui.show_weather(**weather)
```

### 3. Use Async Operations

Don't block on slow operations.

```python
from concurrent.futures import ThreadPoolExecutor

class MySkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executor = ThreadPoolExecutor(max_workers=2)

    def handle_news(self, message):
        """Fetch news without blocking GUI."""
        # Show loading screen immediately
        self.gui.show_generic(
            data={"type": "loading", "message": "Fetching news..."}
        )

        # Fetch news in background
        self.executor.submit(self.fetch_and_display_news)

    def fetch_and_display_news(self):
        """Fetch news (slow) then show."""
        articles = self.fetch_news()  # Slow operation
        # When done, show results
        self.gui.show_news(articles=articles)
```

### 4. Batch Updates

Update session data instead of full page reloads.

```python
class MusicSkill(OVOSSkill):
    def update_playback_position(self, elapsed):
        """Update elapsed time without full page reload."""
        # ❌ Slow: Full page reload every 100ms
        self.gui.show_music(
            title=self.track["title"],
            artist=self.track["artist"],
            elapsed=elapsed
        )

        # ✅ Fast: Just update the changed field
        self.gui.set_context({
            "elapsed": elapsed,
            "progress": int((elapsed / self.duration) * 100)
        })
```

### 5. Lazy Load Resources

Load images and data only when needed.

```python
class GallerySkill(OVOSSkill):
    def handle_show_gallery(self, message):
        """Show gallery without loading all images."""
        # Just the URLs, not the actual image data
        items = [
            {
                "title": img["title"],
                "image_url": img["url"],  # URL, not image data
                "thumbnail_url": img["thumb_url"]  # Use thumbnails
            }
            for img in self.gallery
        ]

        self.gui.show_grid(items=items)

        # Load full-res images only when user selects
        self.gui.register_handler(
            "gallery.item_selected",
            self.on_item_selected
        )

    def on_item_selected(self, message):
        """Load full image when selected."""
        index = message.data.get("selected")
        image_url = self.gallery[index]["url"]

        self.gui.show_image(image=image_url)
```

---

## Adapter Optimization

### 1. Implement Incremental Rendering

Render the first part of the page quickly, then fill in details.

```qml
// Example QML in adapter
Rectangle {
    width: 800
    height: 600

    // Show immediately
    Text {
        text: "Loading news..."
        anchors.top: parent.top
    }

    // Load images as they arrive
    ListView {
        model: newsModel
        delegate: NewsItemDelegate {
            // Initially show just title
            // Lazily load image as it becomes visible
        }
    }
}
```

### 2. Reuse Components

Don't recreate widgets for every page.

```qml
// ❌ Bad: Destroy and recreate
Loader {
    sourceComponent: newsListComponent
}

// ✅ Good: Update existing widget
ListView {
    model: updatedNewsModel  // Just change the model
}
```

### 3. Minimize Re-renders

Only redraw what changed.

```qml
// ❌ Bad: Update entire page
Rectangle {
    Component.onCompleted: {
        updateUI()
        updateUI()
        updateUI()
    }
}

// ✅ Good: Update only changed fields
Rectangle {
    Text {
        text: root.elapsed  // Bindings trigger on change only
    }
}
```

### 4. Use Efficient Layouts

Complex layouts are slow.

```qml
// ❌ Slow: Column with many nested anchors
Column {
    anchors.fill: parent
    Repeater {
        model: 1000
        delegate: Item {
            anchors.left: parent.left
            anchors.right: parent.right
            // Complex positioning
        }
    }
}

// ✅ Fast: ListView with delegates
ListView {
    anchors.fill: parent
    model: 1000
    delegate: Text {
        text: modelData
    }
}
```

---

## Network Optimization

### 1. Compress Payloads

For slow networks, compress large data.

```python
import json
import gzip
import base64

class MySkill(OVOSSkill):
    def send_large_data(self, data):
        """Compress data before sending."""
        # Serialize
        json_data = json.dumps(data)

        # Compress
        compressed = gzip.compress(json_data.encode())

        # Encode for transmission
        encoded = base64.b64encode(compressed).decode()

        self.gui.show_generic(
            data={"compressed": encoded}
        )
```

### 2. Implement Pagination

Don't send all results at once.

```python
class SearchSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = []
        self.current_page = 0
        self.page_size = 20

    def handle_search(self, message):
        """Search and show first page."""
        query = message.data.get("query")
        self.results = self.search(query)
        self.current_page = 0

        self.show_results_page()

    def show_results_page(self):
        """Show current page of results."""
        start = self.current_page * self.page_size
        end = start + self.page_size

        page_results = self.results[start:end]

        self.gui.show_list(
            items=[r["title"] for r in page_results],
            # Show pagination info
            footer=f"Page {self.current_page + 1} of {self.total_pages}"
        )

        self.gui.register_handler(
            "search.next_page",
            self.on_next_page
        )

    def on_next_page(self, message):
        """Load next page."""
        self.current_page += 1
        self.show_results_page()
```

### 3. Use CDNs for Static Content

Link to images on CDNs instead of sending them.

```python
# ❌ Bad: Encode image as base64
import base64
with open("icon.png", "rb") as f:
    encoded = base64.b64encode(f.read()).decode()
self.gui.show_image(image=f"data:image/png;base64,{encoded}")

# ✅ Good: Use URL from CDN
self.gui.show_image(
    image="https://cdn.example.com/icon.png"
)
```

---

## Device-Specific Optimization

### For Raspberry Pi

```python
class RaspberryPiOptimizedSkill(OVOSSkill):
    def initialize(self):
        """Detect and adapt for Raspberry Pi."""
        # Check available memory
        import psutil
        memory = psutil.virtual_memory().available

        if memory < 512 * 1024 * 1024:  # Less than 512MB
            self.use_lightweight_mode = True

    def handle_intent(self, message):
        """Use lightweight rendering on Pi."""
        if self.use_lightweight_mode:
            # Show minimal data
            self.gui.show_text(
                title="Result",
                text="Processing..."  # Keep it simple
            )
        else:
            # Show full-featured display
            self.gui.show_generic(data={...})
```

### For Smart Displays

```python
class SmartDisplaySkill(OVOSSkill):
    def initialize(self):
        """Optimize for smart displays."""
        # Check screen resolution
        self.is_small_screen = True  # Default

    def handle_intent(self, message):
        """Adapt layout for small screen."""
        if self.is_small_screen:
            # Larger text, fewer items
            self.gui.show_list(
                items=[
                    "Option 1",
                    "Option 2"
                    # Just 2 options for small screen
                ]
            )
        else:
            # Normal display
            self.gui.show_list(items=[...])
```

---

## Memory Management

### 1. Limit Cache Size

Prevent memory from growing unbounded.

```python
class CachedSkill(OVOSSkill):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}
        self.max_cache_size = 10  # Limit to 10 items

    def cache_result(self, key, value):
        """Add to cache with size limit."""
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = value
```

### 2. Use Generators for Large Data

Don't load all data into memory.

```python
def iter_articles(self):
    """Yield articles one at a time."""
    for i in range(1000):
        yield self.fetch_article(i)

def handle_news(self, message):
    """Process articles one at a time."""
    for article in self.iter_articles():
        # Process
        pass
```

### 3. Monitor Memory Usage

```python
import psutil

class MySkill(OVOSSkill):
    def check_memory(self):
        """Log memory usage."""
        process = psutil.Process()
        memory = process.memory_info().rss / 1024 / 1024  # MB

        if memory > 100:  # Alert at 100MB
            self.log.warning(f"High memory: {memory:.0f}MB")
```

---

## Benchmarking

### Profile Your Skill

```python
import cProfile
import pstats

class MySkill(OVOSSkill):
    def profile_method(self):
        """Profile a slow method."""
        prof = cProfile.Profile()
        prof.enable()

        # Your code here
        self.slow_operation()

        prof.disable()
        stats = pstats.Stats(prof)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
```

### Benchmark Page Load Time

```python
import timeit

time_ms = timeit.timeit(
    lambda: self.handle_weather_intent(None),
    number=10
) * 1000 / 10

print(f"Average page load: {time_ms:.0f}ms")
```

---

## Bottleneck Analysis

Common bottlenecks and solutions:

| Bottleneck | Cause | Solution |
|------------|-------|----------|
| **Slow page load** | Large payload or slow API | Cache data, paginate, async fetch |
| **Slow rendering** | Complex QML or many widgets | Simplify layout, use ListView |
| **High memory** | Unbounded cache or leaks | Limit cache size, cleanup |
| **Slow updates** | Full page reload for small changes | Use session context updates |
| **Network lag** | Slow upload/download | Compress, paginate, lazy load |

---

## Checklist

Before releasing a skill:

- [ ] Page show latency < 500ms
- [ ] Payload size < 500KB
- [ ] Memory usage < 100MB
- [ ] Caching implemented for external APIs
- [ ] Async operations for slow operations
- [ ] Images are URLs, not embedded
- [ ] No memory leaks (monitor over 1 hour)
- [ ] Works on slow networks (test with throttling)

---

## Tools

```bash
# Monitor memory
watch -n 1 'ps aux | grep ovos'

# Check network latency
ping messagebus_host

# Throttle network (Linux)
tc qdisc add dev eth0 root tbf rate 1mbit burst 32kbit latency 400ms

# Profile with py-spy
pip install py-spy
py-spy record -o profile.svg -- ovos-gui-service
```

---

## See Also

- **[Monitoring & Debugging](monitoring.md)** — Profiling tools
- **[Skill GUI Development](skill-gui-development.md)** — Best practices
- **[Adapter Plugin System](adapter-plugins.md)** — Adapter optimization

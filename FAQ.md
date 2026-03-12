# FAQ — ovos-gui

## What is the relationship between ovos-gui and the Qt clients (mycroft-gui-qt5, mycroft-gui-qt6)?

`ovos-gui` is the central GUI service running on the OVOS device. It communicates with Qt clients through **adapter plugins**. The `ovos-legacy-mycroft-gui-plugin` implements the mycroft gui protocol (WebSocket on port 18181). Both mycroft-gui-qt5 and mycroft-gui-qt6 connect through this same adapter — the adapter is shared, not per-client.

## Why is the adapter called "legacy" if it is still actively used?

The word "legacy" refers to the protocol's **Mycroft AI origins**, not its current maintenance status. The protocol predates OVOS and was designed by the original Mycroft project. It remains the only production adapter available today.

## Can I use old pre-OVOS mycroft-gui binaries with ovos-gui?

No. Pre-OVOS `mycroft-gui` binaries are **incompatible**. You must recompile from current source (mycroft-gui-qt5 or mycroft-gui-qt6) and use the latest ovos-gui service.

## What is the legacy QML pattern?

The original Mycroft AI approach had skills ship arbitrary QML files over the wire at runtime using `show_pages`. OVOS replaced this with bundled system templates (SYSTEM_text, SYSTEM_weather, SYSTEM_ocp_now_playing, etc.) where skills send structured data instead of UI code.

## How do skills display GUI content in OVOS?

Skills use the template system. Instead of shipping QML, they call methods like `self.gui.show_page("SYSTEM_text")` and pass structured data. The Qt client renders the template locally. See `docs/skill-development/templates.md` for the full template reference.

## Where is the documentation hub?

Start at `docs/index.md` which provides role-based navigation paths for skill developers, adapter developers, system integrators, and contributors.

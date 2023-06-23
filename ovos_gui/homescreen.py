from typing import List, Optional

from ovos_bus_client import Message, MessageBusClient
from ovos_bus_client.message import dig_for_message
from ovos_config.config import Configuration, update_mycroft_config

from ovos_utils.log import LOG, deprecated, log_deprecation

from ovos_gui.namespace import NamespaceManager
from threading import Thread


class HomescreenManager(Thread):
    def __init__(self, bus: MessageBusClient, gui: NamespaceManager):
        super().__init__()
        self.bus = bus
        self.gui = gui
        self.homescreens: List[dict] = []
        self.mycroft_ready = False
        # TODO: If service starts after `mycroft_ready`,
        #       homescreen is never shown
        self.bus.on('homescreen.manager.add', self.add_homescreen)
        self.bus.on('homescreen.manager.remove', self.remove_homescreen)
        self.bus.on('homescreen.manager.list', self.get_homescreens)
        self.bus.on("homescreen.manager.get_active",
                    self.handle_get_active_homescreen)
        self.bus.on("homescreen.manager.set_active",
                    self.handle_set_active_homescreen)
        self.bus.on("homescreen.manager.disable_active",
                    self.disable_active_homescreen)
        self.bus.on("mycroft.mark2.register_idle",
                    self.register_old_style_homescreen)
        self.bus.on("homescreen.manager.show_active", self.show_homescreen)
        self.bus.on("mycroft.ready", self.set_mycroft_ready)

    def run(self):
        """
        Start the Manager after it has been constructed.
        """
        self.reload_homescreens_list()

    def add_homescreen(self, message: Message):
        """
        Handle `homescreen.manager.add` and add the requested homescreen if it
        has not yet been added.
        @param message: Message containing homescreen id/class to add
        """
        homescreen_id = message.data["id"]
        homescreen_class = message.data["class"]

        if any((homescreen['id'] == homescreen_id
                for homescreen in self.homescreens)):
            LOG.info(f"Requested homescreen_id already exists: {homescreen_id}")
        else:
            LOG.info(f"Homescreen Manager: Adding Homescreen {homescreen_id}")
            self.homescreens.append(message.data)

        self.show_homescreen_on_add(homescreen_id, homescreen_class)

    def remove_homescreen(self, message: Message):
        """
        Handle `homescreen.manager.remove` and remove the requested homescreen
        if it exists
        @param message: Message containing homescreen id to remove
        """
        homescreen_id = message.data["id"]
        LOG.info(f"Homescreen Manager: Removing Homescreen {homescreen_id}")
        for h in self.homescreens:
            if homescreen_id == h["id"]:
                self.homescreens.remove(h)

    def get_homescreens(self, message: Message):
        """
        Handle `homescreen.manager.list` and emit a response with loaded
        homescreens.
        :param message: Message requesting homescreens
        """
        self.bus.emit(message.response({"homescreens": self.homescreens}))

    def handle_get_active_homescreen(self, message: Message):
        """
        Handle `homescreen.manager.get_active` and emit a response with the
        active homescreen
        @param message: Message requesting active homescreen
        """
        self.bus.emit(message.response(
            {"homescreen": self.get_active_homescreen()}))

    def handle_set_active_homescreen(self, message: Message):
        """
        Handle `homescreen.manager.set_active` requests to change the configured
        homescreen and update configuration.
        @param message: Message containing requested homescreen ID
        """
        new_homescreen = message.data.get("id")
        LOG.debug(f"Requested updating homescreen to: {new_homescreen}")
        self.set_active_homescreen(new_homescreen)

    def get_active_homescreen(self) -> Optional[dict]:
        """
        Get the active homescreen according to configuration if it is loaded
        @return: Loaded homescreen with an ID matching configuration
        """
        enclosure_config = Configuration().get("gui") or {}
        active_homescreen = enclosure_config.get("idle_display_skill")
        LOG.debug(f"Homescreen Manager: Active Homescreen {active_homescreen}")
        for h in self.homescreens:
            if h["id"] == active_homescreen:
                return active_homescreen

    def set_active_homescreen(self, homescreen_id: str):
        """
        Update the configured `idle_display_skill`
        @param homescreen_id: new `idle_display_skill`
        """
        # TODO: Validate requested homescreen_id
        if Configuration().get("gui",
                               {}).get("idle_display_skill") != homescreen_id:
            LOG.info(f"Updating configured idle_display_skill to "
                     f"{homescreen_id}")
            new_config = {"gui": {"idle_display_skill": homescreen_id}}
            update_mycroft_config(new_config, bus=self.bus)

    def reload_homescreens_list(self):
        """
        Emit a request for homescreens to register via the Messagebus
        """
        LOG.info("Homescreen Manager: Reloading Homescreen List")
        self.collect_old_style_homescreens()
        self.bus.emit(Message("homescreen.manager.reload.list"))

    def show_homescreen_on_add(self, homescreen_id: str, homescreen_class: str):
        """
        Check if a homescreen should be displayed immediately upon addition
        @param homescreen_id: ID of added homescreen
        @param homescreen_class: "class" (IdleDisplaySkill, MycroftSkill)
            of homescreen
        """
        if not self.mycroft_ready:
            LOG.debug("Not ready yet, don't display")
            return
        LOG.debug(f"Checking {homescreen_id}")
        if self.get_active_homescreen() != homescreen_id:
            # Added homescreen isn't the configured one, do nothing
            return

        if homescreen_class == "IdleDisplaySkill":
            LOG.debug(f"Displaying Homescreen {homescreen_id}")
            self.bus.emit(Message("homescreen.manager.activate.display",
                                  {"homescreen_id": homescreen_id}))
        elif homescreen_class == "MycroftSkill":
            log_deprecation(f"Homescreen skills should register listeners for "
                            f"`homescreen.manager.activate.display`. "
                            f"`{homescreen_id}.idle` messages will be removed.",
                            "0.1.0")
            LOG.debug(f"Displaying Homescreen {homescreen_id}")
            self.bus.emit(Message(f"{homescreen_id}.idle"))

    def disable_active_homescreen(self, message: Message):
        """
        Handle `homescreen.manager.disable_active` requests by configuring the
        `idle_display_skill` as None.
        @param message: Message requesting homescreen disable
        """
        # TODO: Is this valid behavior?
        if Configuration().get("gui", {}).get("idle_display_skill"):
            LOG.info(f"Disabling idle_display_skill!")
            new_config = {"gui": {"idle_display_skill": None}}
            update_mycroft_config(new_config, bus=self.bus)

    def show_homescreen(self, message: Optional[Message] = None):
        """
        Handle a request to show the homescreen.
        @param message: Optional `homescreen.manager.show_active` Message
        """
        active_homescreen = self.get_active_homescreen()
        LOG.debug(f"Requesting activation of {active_homescreen}")
        for h in self.homescreens:
            if h.get("id") == active_homescreen:
                LOG.debug(f"matched homescreen skill: {h}")
                message = message or dig_for_message() or Message("")
                if h["class"] == "IdleDisplaySkill":
                    LOG.debug(f"Displaying Homescreen {active_homescreen}")
                    self.bus.emit(message.forward(
                        "homescreen.manager.activate.display",
                        {"homescreen_id": active_homescreen}))
                elif h["class"] == "MycroftSkill":
                    LOG.debug(f"Displaying Homescreen {active_homescreen}")
                    self.bus.emit(message.forward(f"{active_homescreen}.idle"))
                else:
                    LOG.error(f"Requested homescreen has an invalid class: {h}")
                return
        LOG.warning(f"Requested {active_homescreen} not found in: "
                    f"{self.homescreens}")

    def set_mycroft_ready(self, message: Message):
        """
        Handle `mycroft.ready` and show the homescreen
        @param message: `mycroft.ready` Message
        """
        self.mycroft_ready = True
        self.show_homescreen()

    # Add compabitility with older versions of the Resting Screen Class

    def collect_old_style_homescreens(self):
        """Trigger collection of older resting screens."""
        # TODO: Deprecate in 0.1.0
        self.bus.emit(Message("mycroft.mark2.collect_idle"))

    @deprecated("`mycroft.mark2.collect_idle` responses are deprecated",
                "0.1.0")
    def register_old_style_homescreen(self, message):
        if "name" in message.data and "id" in message.data:
            super_class_name = "MycroftSkill"
            super_class_object = message.data["name"]
            skill_id = message.data["id"]
            _homescreen_entry = {"class": super_class_name,
                                 "name": super_class_object, "id": skill_id}
            LOG.debug(f"Homescreen Manager: Adding OLD Homescreen {skill_id}")
            self.add_homescreen(
                Message("homescreen.manager.add", _homescreen_entry))
        else:
            LOG.error("Malformed idle screen registration received")

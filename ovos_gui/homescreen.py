from threading import Thread
from typing import List, Optional

from ovos_config.config import Configuration, update_mycroft_config
from ovos_utils.log import LOG, log_deprecation

from ovos_bus_client import Message, MessageBusClient
from ovos_bus_client.message import dig_for_message


class HomescreenManager(Thread):
    def __init__(self, bus: MessageBusClient):
        super().__init__()
        self.bus = bus
        self.homescreens: List[dict] = []

        self.bus.on('homescreen.manager.add', self.add_homescreen)
        self.bus.on('homescreen.manager.remove', self.remove_homescreen)
        self.bus.on('homescreen.manager.list', self.get_homescreens)
        self.bus.on("homescreen.manager.get_active", self.handle_get_active_homescreen)
        self.bus.on("homescreen.manager.set_active", self.handle_set_active_homescreen)
        self.bus.on("homescreen.manager.disable_active", self.disable_active_homescreen)
        self.bus.on("homescreen.manager.show_active", self.show_homescreen)

    def run(self):
        """
        Start the Manager after it has been constructed.
        """
        self.reload_homescreens_list()
        self.show_homescreen()

    def add_homescreen(self, message: Message):
        """
        Handle `homescreen.manager.add` and add the requested homescreen if it
        has not yet been added.
        @param message: Message containing homescreen id to add
        """
        homescreen_id = message.data["id"]

        if any((homescreen['id'] == homescreen_id
                for homescreen in self.homescreens)):
            LOG.info(f"Requested homescreen_id already exists: {homescreen_id}")
        else:
            LOG.info(f"Homescreen Manager: Adding Homescreen {homescreen_id}")
            self.homescreens.append(message.data)

        self.show_homescreen_on_add(homescreen_id)

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
        gui_config = Configuration().get("gui") or {}
        active_homescreen = gui_config.get("idle_display_skill")
        if not active_homescreen:
            LOG.info("No homescreen enabled in mycroft.conf")
            return
        LOG.info(f"Active Homescreen: {active_homescreen}")
        for h in self.homescreens:
            if h["id"] == active_homescreen:
                return active_homescreen
        LOG.error(f"{active_homescreen} not loaded!")

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
        self.bus.emit(Message("homescreen.manager.reload.list"))

    def show_homescreen_on_add(self, homescreen_id: str):
        """
        Check if a homescreen should be displayed immediately upon addition
        @param homescreen_id: ID of added homescreen
        """
        LOG.debug(f"Checking {homescreen_id}")
        if self.get_active_homescreen() != homescreen_id:
            # Added homescreen isn't the configured one, do nothing
            return

        LOG.info(f"Displaying Homescreen {homescreen_id}")
        self.bus.emit(Message("homescreen.manager.activate.display",
                              {"homescreen_id": homescreen_id}))

    def disable_active_homescreen(self, message: Message):
        """
        Handle `homescreen.manager.disable_active` requests by configuring the
        `idle_display_skill` as None.
        @param message: Message requesting homescreen disable
        """
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
        if not active_homescreen:
            LOG.info("No active homescreen to display")
            return
        LOG.info(f"Requesting activation of {active_homescreen}")
        for h in self.homescreens:
            if h.get("id") == active_homescreen:
                LOG.debug(f"matched homescreen skill: {h}")
                message = message or dig_for_message() or Message("")
                LOG.debug(f"Displaying Homescreen {active_homescreen}")
                self.bus.emit(message.forward(
                    "homescreen.manager.activate.display",
                    {"homescreen_id": active_homescreen}))
                break
        else:
            LOG.warning(f"Requested {active_homescreen} not found in: "
                        f"{self.homescreens}")

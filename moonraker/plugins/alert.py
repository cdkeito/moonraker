# This file is provided as-is.
# This file may be distributed under the terms of the GNU GPLv3 license.
# ArcWelderConsole project site is https://github.com/FormerLurker/ArcWelderLib

# To enable, add [alert] to moonraker config file "moonraker.conf"

import os
import logging
import json


class Alert:
    def __init__(self, config):
        self.server = config.get_server()
        self.currentState = None

        self.server.register_event_handler("server:status_update", self._handle_status_update)

    async def _handle_status_update(self, status):
        logging.info(f"cmd: {status}")


def load_plugin(config):
    return Alert(config)

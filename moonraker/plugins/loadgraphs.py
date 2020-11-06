# This file is provided as-is.
# This file may be distributed under the terms of the GNU GPLv3 license.
# ArcWelderConsole project site is https://github.com/FormerLurker/ArcWelderLib

# To enable, add [arcwelder] to moonraker config file "moonraker.conf"

import os
import logging

VALID_GCODE_EXTS = ['gcode', 'g', 'gco']
FULL_ACCESS_ROOTS = ["gcodes", "config"]
ARCWELDER_EXEC = os.path.join(os.path.dirname(__file__), "../../scripts/ArcWelderConsole")


class LoadGraphs:
    def __init__(self, config):
        self.server = config.get_server()
        self.file_manager = self.server.lookup_plugin('file_manager')

        self.graphstatsPath = config.get("graphstatsPath", "~/klipper/scripts/graphstats.py")
        self.graphstatsTimeOut = int(config.get("graphstatsTimeOut", "3600"))
        self.klippyLogPath = config.get("klippyLogPath", "/tmp/klippy.log")
        self.targetDir = config.get("targetDir", "/home/pi/mainsail/img/loadgraphs")
        self.targetUrl = config.get("targetUrl", "/img/loadgraphs")

        logging.info(f"graphstatsPath: {self.graphstatsPath}")
        logging.info(f"graphstatsTimeOut: {self.graphstatsTimeOut}")
        logging.info(f"klippyLogPath: {self.klippyLogPath}")
        logging.info(f"targetDir: {self.targetDir}")
        logging.info(f"targetUrl: {self.targetUrl}")

        # TODO get mcu list from config
        self.mcu = {"mcu": "mcu", "z": "z"}
        self.graphTypes = {"mcu": "", "sys": "-s"}

        if not os.path.exists(self.graphstatsPath):
            raise self.server.error(f"The graphstatsPath don't exists: {self.graphstatsPath}")
        if not os.path.exists(self.klippyLogPath):
            raise self.server.error(f"The klippyLogPath don't exists: {self.klippyLogPath}")
        # if self.targetDir is None:
        #     raise self.server.error("Missing traget directory configuration: targetDir")

        # Register file management endpoints
        self.server.register_endpoint("/loadgraohs/regen/all", ['POST'], self._handle_regen, protocol=["http"])

    async def _handle_regen(self, path, method, args):
        if not os.path.exists(self.targetDir):
            os.makedirs(self.targetDir, 0o777, True)

        shell_command = self.server.lookup_plugin('shell_command')

        outputList = {}
        for gtType in self.graphTypes.keys():
            for mcu in self.mcu.keys():
                cmd = f"{self.graphstatsPath} {self.klippyLogPath} -o {self.targetDir}/loadgraph-{gtType}_{mcu}.png -m {mcu} {self.graphTypes[gtType]}"
                logging.info(f"cmd ({gtType}->{mcu}): {cmd}")
                scmd = shell_command.build_shell_command(cmd, None)
                outputList[f"{gtType}_{mcu}"] = f"{self.targetUrl}/loadgraph-{gtType}_{mcu}.png"
                try:
                    await scmd.run(timeout=self.graphstatsTimeOut, verbose=True)
                except Exception:
                    logging.exception(f"Error running cmd '{cmd}'")

        return outputList


def load_plugin(config):
    return LoadGraphs(config)

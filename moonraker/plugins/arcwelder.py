# This file is provided as-is.
# This file may be distributed under the terms of the GNU GPLv3 license.
# ArcWelderConsole project site is https://github.com/FormerLurker/ArcWelderLib

# To enable, add [arcwelder] to moonraker config file "moonraker.conf"

import os
import logging
import json

VALID_GCODE_EXTS = ['gcode', 'g', 'gco']
FULL_ACCESS_ROOTS = ["gcodes", "config"]
ARCWELDER_EXEC = os.path.join(os.path.dirname(__file__), "../../scripts/ArcWelderConsole")


class ArcWelder:
    def __init__(self, config):
        self.server = config.get_server()
        self.file_manager = self.server.lookup_plugin('file_manager')

        # Register file management endpoints
        self.server.register_endpoint("/arcwelder/file/arcwelder", ['POST'], self._handle_file_arcwelder, protocol=["http"])

    async def _handle_file_arcwelder(self, path, method, args):
        source = args.get("source")
        destination = args.get("dest")
        maxradius = args.get("maxradius")
        resolution = args.get("resolution")
        if source is None:
            raise self.server.error("File arcwelder request missing source")
        if destination is None:
            raise self.server.error("File arcwelder request missing destination")
        if maxradius is None:
            maxradius = 1000000.00
        if resolution is None:
            resolution = 0.05

        if not source.startswith("gcodes/"):
            source = "gcodes/" + source
        if not destination.startswith("gcodes/"):
            destination = "gcodes/" + destination

        ext = source[source.rfind('.') + 1:]
        if ext not in VALID_GCODE_EXTS:
            raise self.server.error("File arcwelder request source not a gcode (" + ", ".join(VALID_GCODE_EXTS) + ")")

        source_base, src_url_path, source_path = self.file_manager._convert_path(source)
        dest_base, dst_url_path, dest_path = self.file_manager._convert_path(destination)
        if dest_base not in FULL_ACCESS_ROOTS:
            raise self.server.error(f"Destination path is read-only: {dest_base}")
        if not os.path.exists(source_path):
            raise self.server.error(f"File {source_path} does not exist")
        if os.path.exists(dest_path):
            raise self.server.error(f"File {dest_base} already exist")

        cmd = f"{ARCWELDER_EXEC} -p -m={maxradius} -r={resolution} {source_path} {dest_path}"
        logging.info(f"cmd: {cmd}")

        shell_command = self.server.lookup_plugin('shell_command')
        scmd = shell_command.build_shell_command(cmd, None)
        try:
            await scmd.run(timeout=3600., verbose=False)
        except Exception:
            logging.exception(f"Error running cmd '{cmd}'")

        return "ok"


def load_plugin(config):
    return ArcWelder(config)

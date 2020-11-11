# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# This file may be distributed under the terms of the GNU GPLv3 license.

# Prerequisites
# /home/pi/moonraker-env/bin/pip install -U discord.py
# https://discordpy.readthedocs.io/en/latest/discord.html#discord-intro

# To enable, add to moonraker config file "moonraker.conf"
# [alert_discord]
# discord_bot_token: your_token_here
# ## discord_is_channel set to True to send to a channel, False for direct messages
# discord_is_channel: True
# discord_id: 123456789
#
# discord_on_printing: True
# discord_text_printing: Voron status printing
#
# discord_on_complete: True
# discord_text_complete: Voron status complete
#
# discord_on_error: True
# discord_text_error: Voron status error

import logging
import discord


class AlertDiscord:
    def __init__(self, config):
        self.config = config
        self.server = config.get_server()

        self.server.register_event_handler("server:status_update", self._handle_status_update)
        self.server.register_event_handler("server:klippy_ready", self._process_klippy_ready)

    def _process_klippy_ready(self):
        logging.info("_process_klippy_ready")
        klippy_apis = self.server.lookup_plugin('klippy_apis')
        res = klippy_apis.subscribe_objects({'print_stats': None}, None)
        # if res is not None and 'print_stats' in res:
        #     self.currentState = res['print_stats']['state']

    def _handle_status_update(self, status):
        discord_on_printing = self.config.getBoolean("discord_on_printing", True)
        discord_on_complete = self.config.getBoolean("discord_on_complete", True)
        discord_on_error = self.config.getBoolean("discord_on_error", True)

        if 'print_stats' in status:
            pstats = status['print_stats']
            # Initialize the state (could be "standby", "printing", "paused", "error", "complete")
            if 'state' in pstats and discord_on_printing:
                if pstats['state'] == "printing":
                    # state just transitioned to printing
                    logging.info(f"print_stats.state: {pstats['state']}")
                    self._sendMessage_printing()
                elif pstats['state'] == "complete" and discord_on_complete:
                    # state just transitioned to complete
                    logging.info(f"print_stats.state: {pstats['state']}")
                    self._sendMessage_complete()
                elif pstats['state'] == "error" and discord_on_error:
                    # state just transitioned to error
                    logging.info(f"print_stats.state: {pstats['state']}")
                    self._sendMessage_error()

    def _sendMessage_printing(self):
        discord_text_printing = self.config.get("discord_text_printing", "Your Voron is printing.")
        self._sendMessage(discord_text_printing)

    def _sendMessage_complete(self):
        discord_text_complete = self.config.get("discord_text_complete", "Your Voron job is complete.")
        self._sendMessage(discord_text_complete)

    def _sendMessage_error(self):
        discord_text_error = self.config.get("discord_text_error", "Your Voron has an error. HELP!")
        self._sendMessage(discord_text_error)

    def _sendMessage(self, discord_text):
        discord_bot_token = self.config.get("discord_bot_token", None)
        if discord_bot_token  is None:
            raise self.server.error("discord_bot_token not configured!")
        discord_is_channel = self.config.getBoolean("discord_is_channel", False)
        discord_id = self.config.get("discord_id", None)
        if discord_id  is None:
            raise self.server.error("discord_id not configured!")

        if discord_is_channel:
            self._sendMessageToChannel(discord_text, discord_id, discord_bot_token)
        else:
            self._sendMessageToUser(discord_text, discord_id, discord_bot_token)

    def _sendMessageToUser(self, discord_text, userid, discord_bot_token):
        client = discord.Client()
        client.run(discord_bot_token)

        try:
            logging.info(f"Sending message: to user {userid}")
            user = client.get_user(userid)
            await user.send(discord_text)
        except Exception as e:
            logging.error("Error: unable to send message to user", e)

    def _sendMessageToChannel(self, discord_text, channelid, discord_bot_token):
        client = discord.Client()
        client.run(discord_bot_token)

        try:
            logging.info(f"Sending message: to channel {channelid}")
            channel = client.get_channel(channelid)
            await channel.send(discord_text)
        except Exception as e:
            logging.error("Error: unable to send message to channel", e)


def load_plugin(config):
    return AlertDiscord(config)

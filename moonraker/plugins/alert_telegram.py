# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# This file may be distributed under the terms of the GNU GPLv3 license.

# Prerequisites
# /home/pi/moonraker-env/bin/pip install -U git+https://github.com/alexander-akhmetov/python-telegram#egg=python-telegram
# current python-telegram 0.12 doesn't support async
# https://my.telegram.org/auth?to=apps%2F

# To enable, add to moonraker config file "moonraker.conf"
# [alert_telegram]
# telegram_api_id: 123456
# telegram_api_hash: 123456
# telegram_bot_token: 123456
# telegram_database_encryption_key: changeme1234!
# telegram_chat_id: 123456
# telegram_code: pin
# telegram_password: password
#
# telegram_on_printing: True
# telegram_text_printing: Voron status printing
#
# telegram_on_complete: True
# telegram_text_complete: Voron status complete
#
# telegram_on_error: True
# telegram_text_error: Voron status error

# Notes
# The library (actually tdlib) stores messages database and received files in the /tmp/.tdlib_files/{phone_number}/.

import logging
from telegram.client import Telegram, AuthorizationState


class AlertTelegram:
    def __init__(self, config):
        self.config = config
        self.server = config.get_server()

        self.server.register_event_handler("server:status_update", self._handle_status_update)
        self.server.register_event_handler("server:klippy_ready", self._process_klippy_ready)

    async def _process_klippy_ready(self):
        logging.info("_process_klippy_ready")
        klippy_apis = self.server.lookup_plugin('klippy_apis')
        res = klippy_apis.subscribe_objects({'print_stats': None}, None)
        # if res is not None and 'print_stats' in res:
        #     self.currentState = res['print_stats']['state']

    async def _handle_status_update(self, status):
        telegram_on_printing = self.config.getBoolean("telegram_on_printing", True)
        telegram_on_complete = self.config.getBoolean("telegram_on_complete", True)
        telegram_on_error = self.config.getBoolean("telegram_on_error", True)

        if 'print_stats' in status:
            pstats = status['print_stats']
            # Initialize the state (could be "standby", "printing", "paused", "error", "complete")
            if 'state' in pstats and telegram_on_printing:
                if pstats['state'] == "printing":
                    # state just transitioned to printing
                    logging.info(f"print_stats.state: {pstats['state']}")
                    self._sendMessage_printing()
                elif pstats['state'] == "complete" and telegram_on_complete:
                    # state just transitioned to complete
                    logging.info(f"print_stats.state: {pstats['state']}")
                    self._sendMessage_complete()
                elif pstats['state'] == "error" and telegram_on_error:
                    # state just transitioned to error
                    logging.info(f"print_stats.state: {pstats['state']}")
                    self._sendMessage_error()

    def _sendMessage_printing(self):
        telegram_text_printing = self.config.get("telegram_text_printing", "Your Voron is printing.")
        self._sendMessage(telegram_text_printing)

    def _sendMessage_complete(self):
        telegram_text_complete = self.config.get("telegram_text_complete", "Your Voron job is complete.")
        self._sendMessage(telegram_text_complete)

    def _sendMessage_error(self):
        telegram_text_error = self.config.get("telegram_text_error", "Your Voron has an error. HELP!")
        self._sendMessage(telegram_text_error)

    def _sendMessage(self, telegram_text):
        telegram_api_id = self.config.get("telegram_api_id", None)
        if telegram_api_id is None:
            raise self.server.error("telegram_api_id not configured!")
        telegram_api_hash = self.config.get("telegram_api_hash", None)
        if telegram_api_hash is None:
            raise self.server.error("telegram_api_hash not configured!")
        telegram_bot_token = self.config.get("telegram_bot_token", None)
        if telegram_bot_token is None:
            raise self.server.error("telegram_bot_token not configured!")
        telegram_database_encryption_key = self.config.get("telegram_database_encryption_key", None)
        if telegram_database_encryption_key is None:
            raise self.server.error("telegram_database_encryption_key not configured!")
        telegram_chat_id = self.config.get("telegram_chat_id", None)
        if telegram_chat_id is None:
            raise self.server.error("telegram_chat_id not configured!")
        telegram_code = self.config.get("telegram_code", None)
        if telegram_code is None:
            raise self.server.error("telegram_code not configured!")
        telegram_password = self.config.get("telegram_password", None)
        if telegram_password is None:
            raise self.server.error("telegram_password not configured!")

        try:
            logging.info(f"Login to telegram")
            tg = Telegram(
                api_id=telegram_api_id,
                api_hash=telegram_api_hash,
                phone=telegram_bot_token,  # you can pass 'bot_token' instead
                database_encryption_key=telegram_database_encryption_key
            )
            state = tg.login(blocking=False)

            if state == AuthorizationState.WAIT_CODE:
                # Telegram expects a pin code
                tg.send_code(telegram_code)
                state = tg.login(blocking=False)  # continue the login process

            if state == AuthorizationState.WAIT_PASSWORD:
                tg.send_password(telegram_password)
                state = tg.login(blocking=False)  # continue the login process

            if state != AuthorizationState.READY:
                raise self.server.error(f"Error at the telegram login. Authorization state: {tg.authorization_state}")

            logging.info(f"Loading chats")
            # if this is the first run, library needs to preload all chats
            # otherwise the message will not be sent
            result = tg.get_chats()
            result.wait()

            logging.info(f"Sending message: to chat {telegram_chat_id}")
            result = tg.send_message(
                chat_id=telegram_chat_id,
                text=telegram_text,
            )

            # `tdlib` is asynchronous, so `python-telegram` always returns you an `AsyncResult` object.
            # You can receive a result with the `wait` method of this object.
            result.wait()
            logging.info(result.update)

            tg.stop()  # you must call `stop` at the end of the script
        except Exception as e:
            logging.error("Error: unable to send message to channel", e)


def load_plugin(config):
    return AlertTelegram(config)

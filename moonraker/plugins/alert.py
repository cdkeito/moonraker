# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# This file may be distributed under the terms of the GNU GPLv3 license.

# To enable, add to moonraker config file "moonraker.conf"
# [alert]
# smtp_host: smtp.gmail.com
# smtp_port: 465
# smtp_use_starttls: False
# smtp_use_ssl: True
# smtp_username: your.email@google.com
# smtp_password: your_application_password
# mail_from: your.email@google.com
# mail_to: your.email@google.com
# mail_subject_printing: Voron status printing
# mail_subject_complete: Voron status complete
# mail_subject_error: Voron status error
# mail_text_printing: Your Voron is printing.
# mail_html_printing: <html><body>Your Voron is printing.</body></html>
# mail_text_complete: Your Voron job is complete.
# mail_html_complete: <html><body>Your Voron job is complete.</body></html>
# mail_text_error: Your Voron has an error. HELP!
# mail_html_error: <html><body>Your Voron has an <b>error</b>.</br><h2>HELP!</h2></body></html>

import logging
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Alert:
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
        if 'print_stats' in status:
            pstats = status['print_stats']
            # Initialize the state (could be "standby", "printing", "paused", "error", "complete")
            if 'state' in pstats:
                if pstats['state'] == "printing":
                    # state just transitioned to printing
                    logging.info(f"print_stats.state: {pstats['state']}")
                    self._sendMail_printing()
                elif pstats['state'] == "complete":
                    # state just transitioned to complete
                    logging.info(f"print_stats.state: {pstats['state']}")
                    self._sendMail_complete()
                elif pstats['state'] == "error":
                    # state just transitioned to error
                    logging.info(f"print_stats.state: {pstats['state']}")
                    self._sendMail_error()

    def _sendMail_printing(self):
        mail_subject_printing = self.config.get("mail_subject_printing", "Voron status")
        mail_text_printing = self.config.get("mail_text_printing", "Your Voron is printing.")
        mail_html_printing = self.config.get("mail_html_printing", "Your Voron is printing.")
        self._sendMail(mail_subject_printing, mail_text_printing, mail_html_printing)

    def _sendMail_complete(self):
        mail_subject_complete = self.config.get("mail_subject_complete", "Voron status")
        mail_text_complete = self.config.get("mail_text_complete", "Your Voron job is complete.")
        mail_html_complete = self.config.get("mail_html_complete", "Your Voron job is complete.")
        self._sendMail(mail_subject_complete, mail_text_complete, mail_html_complete)

    def _sendMail_error(self):
        mail_subject_error = self.config.get("mail_subject_error", "Voron status")
        mail_text_error = self.config.get("mail_text_error", "Your Voron has an error. HELP!")
        mail_html_error = self.config.get("mail_html_error", "Your Voron has an error. HELP!")
        self._sendMail(mail_subject_error, mail_text_error, mail_html_error)

    def _sendMail(self, mail_subject, mail_text, mail_html):
        smtp_host = self.config.get("smtp_host", "localhost")
        smtp_port = int(self.config.get("smtp_port", "25"))
        smtp_username = self.config.get("smtp_username", None)
        smtp_password = self.config.get("smtp_password", None)
        smtp_use_starttls = self.config.getboolean("smtp_use_starttls", False)
        smtp_use_ssl = self.config.getboolean("smtp_use_ssl", False)

        mail_from = self.config.get("mail_from", "root@localhost")
        mail_to = self.config.get("mail_to", "owner@localhost")

        logging.info(f"Sending email: from {mail_from} to {mail_to} with subject {mail_subject}")

        try:
            msg = MIMEMultipart("alternative")
            msg['From'] = mail_from
            msg['To'] = mail_to
            msg['Subject'] = mail_subject

            part1 = MIMEText(mail_text, "plain")
            part2 = MIMEText(mail_html, "html")
            msg.attach(part1)
            msg.attach(part2)

            if smtp_use_ssl:
                logging.info(f"Connetting to email SSL server {smtp_host}:{smtp_port}")
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as s:
                    s.ehlo()
                    if smtp_username is not None:
                        logging.info(f"Authenticating to email SSL server {smtp_username}:*****")
                        s.login(smtp_username, smtp_password)
                    s.sendmail(mail_from, mail_to, msg.as_string())
                    logging.info("Email sent")
            else:
                logging.info(f"Connetting to email server {smtp_host}:{smtp_port}")
                with smtplib.SMTP(smtp_host, smtp_port) as s:
                    s.ehlo()
                    if smtp_use_starttls:
                        logging.info(f"Sending STARTTLS to email SSL server {smtp_host}:{smtp_port}")
                        context = ssl.create_default_context()
                        s.starttls(context=context)
                        s.ehlo()
                    if smtp_username is not None:
                        logging.info(f"Authenticating to email SSL server {smtp_username}:*****")
                        s.login(smtp_username, smtp_password)
                    s.sendmail(mail_from, mail_to, msg.as_string())
                    logging.info("Email sent")
        except Exception as e:
            logging.error("Error: unable to send email", e)


def load_plugin(config):
    return Alert(config)

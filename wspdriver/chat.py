import time
from selenium.common.exceptions import WebDriverException

from wspdriver.message import WhatsappMessage


class WhatsAppChat(object):

    def __init__(self, chat_element, whatsapp_driver):
        self.chat_element = chat_element
        self.whatsapp_driver = whatsapp_driver
        self.web_driver = whatsapp_driver.web_driver

    def select(self):

        self.web_driver.execute_script(
            'arguments[0].scrollIntoView()',
            self.chat_element
        )
        time.sleep(0.2)  # Scroll...
        try:
            self.chat_element.click()
        except WebDriverException as e:
            print(self.name)
            raise e

    def ensure_scroll_to_bottom(self):

        incoming_btn = self.whatsapp_driver.find_element_by_selector(
            '.incoming-msgs'
        )
        if incoming_btn:
            incoming_btn.click()
            time.sleep(0.5)

    def get_messages(self):

        self.select()
        self.ensure_scroll_to_bottom()
        messages = self.web_driver.find_elements_by_css_selector(
            '.pane-chat-msgs .message-chat'
        )
        for message in messages:
            yield WhatsappMessage(message)

    @property
    def name(self):
        return self.chat_element.find_element_by_css_selector(
            '.chat-title'
        ).text

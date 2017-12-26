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

    def get_messages(self):

        self.select()
        self.whatsapp_driver.ensure_scroll_to_chat_bottom()
        messages = self.web_driver.find_elements_by_css_selector(
            '.pane-chat-msgs .message'
        )
        for message_element in messages:
            yield WhatsappMessage.build(message_element, self.whatsapp_driver)

    @property
    def name(self):
        return self.chat_element.find_element_by_css_selector(
            '.chat-title'
        ).text

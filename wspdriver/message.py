import hashlib
import re

from datetime import datetime

from bs4 import BeautifulSoup


class WhatsappMessage(object):

    @classmethod
    def build(cls, message_element, whatsapp_driver):

        classes = message_element.get_attribute('class')
        if 'message-chat' in classes:
            return WSPTextMessage(message_element, whatsapp_driver)

        elif 'message-image' in classes:
            return WSPImageMessage(message_element, whatsapp_driver)

        elif 'message-gif' in classes:
            return WSPGIFMessage(message_element, whatsapp_driver)

        elif 'message-system' in classes:
            return WSPSystemMessage(message_element, whatsapp_driver)

        raise UnknownMessageTypeException(classes)

    def __init__(self, message_element, whatsapp_driver):

        self.driver = whatsapp_driver
        classes = message_element.get_attribute('class')
        self.is_outbound = 'message-out' in classes

    def is_system_message(self):
        return False

    def is_image(self):
        return False

    def is_gif(self):
        return False


class UnknownMessageTypeException(Exception):
    pass


class WSPTextMessage(WhatsappMessage):

    METADATA_REGEX = re.compile(r'\[(\d+):(\d+),\s(\d+)/(\d+)/(\d+)\]\s(.*):')

    def __init__(self, message_element, driver):

        super(WSPTextMessage, self).__init__(message_element, driver)
        bubble = message_element.find_element_by_css_selector('.bubble')
        metadata = bubble.get_attribute('data-pre-plain-text')
        self.datetime, self.author_name = self.parse_metadata(metadata)

        bubble_text = message_element.find_element_by_css_selector(
            '.bubble .selectable-text'
        )
        self.text = self.transform_emojis_to_text(bubble_text)

        to_hash = '{}{}{}'.format(
            self.datetime, self.author_name, self.text
        )
        self.id = hashlib.md5(to_hash.encode()).hexdigest()

    def transform_emojis_to_text(self, bubble_element):

        html = bubble_element.get_attribute('outerHTML')
        dom = BeautifulSoup(html, 'html.parser')
        for img in dom.find_all('img'):
            img.replace_with(img['data-plain-text'])
        return dom.text

    def __str__(self):
        return '[{}] {}: {}'.format(
            self.datetime,
            'Me' if self.is_outbound else self.author_name,
            self.text
        )

    @classmethod
    def parse_metadata(cls, data_text):
        match = re.match(cls.METADATA_REGEX, data_text)
        hour = int(match.group(1))
        minute = int(match.group(2))
        day = int(match.group(3))
        month = int(match.group(4))
        year = int(match.group(5))
        dt = datetime(year, month, day, hour, minute)
        name = match.group(6)
        return dt, name


class WSPImageMessage(WhatsappMessage):

    def __init__(self, message_element, driver):
        super(WSPImageMessage, self).__init__(message_element, driver)

        self.thumbnail = message_element.find_element_by_css_selector(
            '.bubble-image .image-thumb img'
        ).get_attribute('src')

        self.time = message_element.find_element_by_css_selector(
            '.bubble-image .bubble-image-meta'
        ).text

        to_hash = '{}{}'.format(
            self.thumbnail, self.time
        )
        self.id = hashlib.md5(to_hash.encode()).hexdigest()

    def image(self):
        return self.driver.get_image(self.thumbnail)

    def __str__(self):
        return '[{}] {}: {}'.format(
            self.time,
            'Me' if self.is_outbound else 'Another',
            self.thumbnail
        )

    def is_image(self):
        return True


class WSPGIFMessage(WhatsappMessage):

    def __init__(self, message_element, driver):
        super(WSPGIFMessage, self).__init__(message_element, driver)

        #TODO: GIF DATA
        self.thumbnail = message_element.find_element_by_css_selector(
            '.bubble-image .image-thumb-gif'
        )

    def is_gif(self):
        return True


class WSPSystemMessage(WhatsappMessage):

    def __init__(self, message_element, driver):
        super(WSPSystemMessage, self).__init__(message_element, driver)

    def is_system_message(self):
        return True

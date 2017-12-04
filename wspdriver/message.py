import hashlib
import re

from datetime import datetime


class WhatsappMessage(object):

    METADATA_REGEX = re.compile(r'\[(\d+):(\d+),\s(\d+)/(\d+)/(\d+)\]\s(.*):')

    def __init__(self, message_element):

        bubble = message_element.find_element_by_css_selector('.bubble')
        metadata = bubble.get_attribute('data-pre-plain-text')
        self.datetime, self.author_name = self.parse_metadata(metadata)

        classes = message_element.get_attribute('class')
        self.is_outbound = 'message-out' in classes

        bubble_text = message_element.find_element_by_css_selector(
            '.bubble .selectable-text'
        )
        self.text = bubble_text.text

        to_hash = '{}{}{}'.format(
            self.datetime, self.author_name, self.text
        )
        self.id = hashlib.md5(to_hash.encode()).hexdigest()

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

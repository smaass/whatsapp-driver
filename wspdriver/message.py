import re

from datetime import datetime


class WhatsappMessage(object):

    METADATA_REGEX = re.compile(r'\[(\d+):(\d+),\s(\d+)/(\d+)/(\d+)\]\s(.*):')
    SINGLE_CHAT_MID_REGEX = re.compile(r'(false|true)_(\d+)@(.*)')
    GROUP_CHAT_MID_REGEX = re.compile(r'(false|true)_(\d+-\d+)@(.*)_(\d+)')

    def __init__(self, message_element):

        bubble = message_element.find_element_by_css_selector('.bubble')
        metadata = bubble.get_attribute('data-pre-plain-text')
        self.datetime, self.author_name = self.parse_metadata(metadata)

        bubble_text = message_element.find_element_by_css_selector(
            '.bubble > .message-text'
        )
        self.text = bubble_text.text

        mid = bubble_text.get_attribute('data-id')
        self.is_outbound, self.id, self.author_phone = self.parse_mid(mid)

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

    @classmethod
    def parse_group_chat_mid(cls, regex_match):

        is_outbound = regex_match.group(1) == 'true'
        group_id = regex_match.group(2)
        mid = regex_match.group(3)
        phone = regex_match.group(4)
        return is_outbound, group_id + mid, phone

    @classmethod
    def parse_single_chat_mid(cls, regex_match):

        is_outbound = regex_match.group(1) == 'true'
        phone = regex_match.group(2)
        mid = regex_match.group(3)
        return is_outbound, mid, phone

    @classmethod
    def parse_mid(cls, message_id):

        regex_match = re.match(cls.SINGLE_CHAT_MID_REGEX, message_id)
        if regex_match is None:
            regex_match = re.match(cls.GROUP_CHAT_MID_REGEX, message_id)
            return cls.parse_group_chat_mid(regex_match)
        else:
            return cls.parse_single_chat_mid(regex_match)

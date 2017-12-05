import base64
import hashlib
import time
from functools import reduce
from io import BytesIO

from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from wspdriver.chat import WhatsAppChat
from wspdriver.message import WhatsappMessage


class WhatsappDriver(object):

    USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
                 '(KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'

    @classmethod
    def start(cls, chrome_driver_path, chrome_data_path):

        options = webdriver.ChromeOptions()
        options.add_argument('--user-data-dir=' + chrome_data_path)
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=650,650')
        options.add_argument('user-agent={}'.format(cls.USER_AGENT))
        web_driver = webdriver.Chrome(
            chrome_options=options,
            executable_path=chrome_driver_path
        )

        return cls(web_driver)

    def __init__(self, web_driver):

        self.web_driver = web_driver
        web_driver.get('https://web.whatsapp.com')
        WebDriverWait(web_driver, 10).until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, 'app-wrapper')
            )
        )
        self.whatsapp_web_version = self.get_wsp_web_version()

    def get_wsp_web_version(self):

        scripts = [
            script.get_attribute('src') for script in
            self.web_driver.find_elements_by_tag_name('script')
        ]

        to_hash = reduce(lambda a, b: a + '|' + b, sorted(scripts), '')
        return hashlib.md5(to_hash.encode()).hexdigest()

    def quit(self):

        self.web_driver.quit()

    def screenshot(self, img_file):

        self.web_driver.get_screenshot_as_file(img_file)

    def capture_login(self):

        login_element = self.web_driver.find_element_by_css_selector(
            '.app-wrapper img'
        )
        login_image_base64 = login_element.get_attribute('src')
        return login_image_base64

    def save_login_as_image(self, filename):

        login_image_base64 = self.get_log_in_code()\
            .replace('data:image/png;base64,', '')\
            .encode('ascii')

        image = Image.open(BytesIO(base64.decodebytes(login_image_base64)))
        image.save(filename)

    def get_log_in_code(self):

        if self.is_logged_in():
            raise AlreadyLoggedInException()

        WebDriverWait(self.web_driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.app-wrapper img')
            )
        )
        return self.capture_login()

    def wait_for_login(self, timeout=None):

        seconds_passed = 0
        while timeout is None or timeout > seconds_passed:
            main = self.web_driver.find_elements_by_class_name(
                'app-wrapper-main'
            )
            if len(main) > 0:
                return
            time.sleep(1)
            seconds_passed += 1

        raise LoginTimeoutError('{} seconds passed'.format(timeout))

    def is_logged_in(self):

        while True:
            main = self.web_driver.find_elements_by_class_name(
                'app-wrapper-main'
            )
            if len(main) > 0:
                return True
            image = self.web_driver.find_elements_by_css_selector(
                '.app-wrapper img'
            )
            if len(image) > 0:
                return False

            time.sleep(0.1)

    def get_unread_chats(self):

        if not self.is_logged_in():
            raise NotLoggedInException()

        chats = self.web_driver.find_elements_by_css_selector('.chat.unread')
        for chat in chats:
            yield WhatsAppChat(chat, self)

    def get_chats(self):

        if not self.is_logged_in():
            raise NotLoggedInException()

        chats = self.web_driver.find_elements_by_css_selector('.chat')
        for chat in chats:
            yield WhatsAppChat(chat, self)

    def get_current_chat_messages(self):

        if not self.is_logged_in():
            raise NotLoggedInException()

        messages = self.web_driver.find_elements_by_css_selector(
            '.pane-chat-msgs .message-chat'
        )
        for message in messages:
            yield WhatsappMessage(message)

    read_messages = set()

    def ensure_no_duplicates(self, messages):

        filtered_messages = [
            message for message in messages
            if message.id not in self.read_messages
        ]
        for message in filtered_messages:
            self.read_messages.add(message.id)
            yield message

    def get_unread_messages(self):

        current_chat = self.get_current_chat_messages()
        yield from self.ensure_no_duplicates(current_chat)

        for chat in self.get_unread_chats():
            yield from self.ensure_no_duplicates(chat.get_messages())

    def open_conversation(self, phone_number):

        if not self.is_logged_in():
            raise NotLoggedInException()

        WebDriverWait(self.web_driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'input.input-search')
            )
        )
        search_box = self.web_driver.find_element_by_css_selector(
            'input.input-search'
        )
        search_box.send_keys(phone_number)
        WebDriverWait(self.web_driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.list-search > span .icon-spinner')
            )
        )
        WebDriverWait(self.web_driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.list-search > span .icon-close-search')
            )
        )
        chat_element = self.web_driver.find_element_by_class_name('chat')
        chat_element.click()

    def send_message(self, phone_number, message):

        self.open_conversation(phone_number)
        input_element = self.web_driver.find_element_by_class_name(
            'pluggable-input'
        )
        input_element.send_keys(message)
        send_button = self.web_driver.find_element_by_css_selector(
            'button.compose-btn-send'
        )
        send_button.click()


class NotLoggedInException(Exception):
    pass


class AlreadyLoggedInException(Exception):
    pass


class LoginTimeoutError(TimeoutError):
    pass

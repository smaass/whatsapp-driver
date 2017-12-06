import base64
import hashlib
import time
from functools import reduce
from io import BytesIO

from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from wspdriver.chat import WhatsAppChat
from wspdriver.message import WhatsappMessage
from wspdriver.user import User


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

    def wait_until(self, finder, css_selector, timeout):

        return WebDriverWait(self.web_driver, timeout).until(
            finder((By.CSS_SELECTOR, css_selector))
        )

    def wait_until_clickable(self, css_selector, timeout=10):

        return self.wait_until(
            EC.element_to_be_clickable,
            css_selector,
            timeout
        )

    def wait_until_located(self, css_selector, timeout=10):

        return self.wait_until(
            EC.presence_of_element_located,
            css_selector,
            timeout
        )

    def quit(self):

        self.web_driver.quit()

    def save_screenshot(self, img_file):

        self.web_driver.get_screenshot_as_file(img_file)

    def get_screenshot(self):

        return self.web_driver.get_screenshot_as_png()

    def save_login_as_image(self, filename):

        login_image_base64 = self.get_log_in_code()\
            .replace('data:image/png;base64,', '')\
            .encode('ascii')

        image = Image.open(BytesIO(base64.decodebytes(login_image_base64)))
        image.save(filename)

    def get_log_in_code(self):

        if self.is_logged_in():
            raise AlreadyLoggedInException()

        login_element = self.wait_until_located('.app-wrapper img')
        login_image_base64 = login_element.get_attribute('src')
        return login_image_base64

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
            logo = self.web_driver.find_elements_by_css_selector(
                'span[data-icon="logo"]'
            )
            if len(logo) > 0:
                return False

            time.sleep(0.1)

    def get_avatar(self, avatar_url):

        self.web_driver.execute_script("window.open('','_blank');")
        windows = self.web_driver.window_handles
        self.web_driver.switch_to_window(windows[1])
        self.web_driver.get(avatar_url)
        img_element = self.wait_until_located('img')
        img_location = img_element.location
        img_size = img_element.size

        image = Image.open(BytesIO(self.get_screenshot()))
        left = img_location['x']
        top = img_location['y']
        right = left + img_size['width']
        bottom = top + img_size['height']
        image.crop((left, top, right, bottom))

        self.web_driver.close()
        self.web_driver.switch_to_window(windows[0])
        return image

    def get_user_data(self):

        if not self.is_logged_in():
            raise NotLoggedInException()

        self.wait_until_clickable('.pane-list-user .avatar').click()
        name = self.wait_until_clickable('.drawer .pluggable-input-body').text

        avatar_element = self.wait_until_clickable('.drawer img')
        avatar_url = avatar_element.get_attribute('src')
        avatar = self.get_avatar(avatar_url)

        time.sleep(0.5)  # Animation...
        ActionChains(self.web_driver)\
            .move_to_element(avatar_element)\
            .click().perform()

        self.wait_until_clickable('li div[title="Ver foto"]').click()
        phone_number = self.wait_until_located('span.emojitext')\
            .text.replace(' ', '').replace('+', '')

        self.wait_until_clickable('span[data-icon="x-viewer"]').click()
        time.sleep(0.6)  # Animation...

        self.wait_until_clickable('.drawer-header .btn-close-drawer').click()
        return User(phone_number, name, avatar)

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

        # search_box = self.wait_until_located('input.input-search')
        search_box = self.wait_until_located('#input-chatlist-search')
        search_box.send_keys(phone_number)
        time.sleep(0.5)
        search_box.send_keys(Keys.RETURN)

        # self.wait_until_located('.list-search > span .icon-spinner')
        # self.wait_until_located('.list-search > span .icon-close-search')

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

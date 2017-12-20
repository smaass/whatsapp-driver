from wspdriver.driver import WhatsappDriver


class REPL(object):

    def __init__(self, driver):
        self.driver = driver
        self.running = True

    def log_in(self):

        print('MUST LOG IN')
        self.driver.save_login_as_image('login.png')
        self.driver.wait_for_login()
        print('LOGGED IN')

    def start(self):

        if not self.driver.is_logged_in():
            self.log_in()

        while self.running:
            user_input = input('>> ')
            result = self.act_on_input(user_input)
            print(result)

        self.driver.quit()

    def act_on_input(self, user_input):

        if user_input == 'exit':
            self.running = False
            return 'Bye'

        if user_input == 'current_chat_messages':
            for message in self.driver.get_current_chat_messages():
                print(message)
            return 'OK.'

        if user_input == 'get_user_data':
            user = self.driver.get_user_data()
            return '{}, {}'.format(user.phone_number, user.name)

        if user_input == 'whatsapp_web_version':
            return self.driver.get_wsp_web_version()

        if user_input == 'get_unread_chat':
            chat = self.driver.get_unread_chat()
            if chat:
                for message in chat.get_messages():
                    print(message)
                return 'Ok.'
            else:
                return 'All chats read.'

        if user_input == 'get_unread_chats':
            # for chat in self.driver.get_unread_chats():
            #     return ''
            return 'All chats read.'

        return 'Command not understood: {}'.format(user_input)


if __name__ == '__main__':

    print('INITIALIZING...')
    driver = WhatsappDriver.start(
        'webdriver/chromedriver',
        'data/whatsapp-driver',
        False
    )

    repl = REPL(driver)
    repl.start()

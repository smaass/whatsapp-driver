from wspdriver.driver import WhatsappDriver

if __name__ == '__main__':

    print('INITIALIZING...')
    driver = WhatsappDriver.start(
        'webdriver/chromedriver',
        'data/whatsapp-driver'
    )
    if not driver.is_logged_in():
        print('MUST LOG IN')
        driver.save_login_as_image('login.png')
        driver.wait_for_login()
        print('LOGGED IN')

    # messages = driver.get_unread_messages()
    # for msg in messages:
    #     print(msg.text)
    # print('SENDING MESSAGE')
    # driver.send_message('56999645308', 'Oli, soy un bot')

    # chats = driver.get_chats()
    # chat = chats.__next__()
    # for message in chat.get_messages():
    #     print(message.id)
    #     print(message)

    user = driver.get_user_data()
    print(user.phone_number, user.name)
    user.avatar.save('avatar.png')
    driver.save_screenshot('demo.png')
    driver.quit()

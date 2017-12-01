from wspdriver.driver import WhatsappDriver

if __name__ == '__main__':
    print('INITIALIZING...')
    driver = WhatsappDriver.start(
        'webdriver/chromedriver',
        'data/whatsapp-driver'
    )
    if not driver.is_logged_in():
        print('MUST LOG IN')
        driver.log_in()
        print('LOGGED IN')
    # messages = driver.get_unread_messages()
    # for msg in messages:
    #     print(msg.text)
    print('SENDING MESSAGE')
    driver.send_message('56999645308', 'Oli, soy un bot')
    driver.screenshot('demo.png')
    driver.quit()

from wspdriver.driver import WhatsappDriver

if __name__ == '__main__':
    driver = WhatsappDriver.start(
        'webdriver/chromedriver',
        'data/whatsapp-driver'
    )
    messages = driver.get_unread_messages()
    for msg in messages:
        print(msg.text)
    driver.screenshot('demo.png')

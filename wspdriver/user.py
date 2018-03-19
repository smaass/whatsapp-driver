class User(object):

    def __init__(self, phone_number, name, avatar):

        self.phone_number = phone_number
        self.name = name
        self.avatar = avatar

    def save_avatar(self, filename):

        self.avatar.save(filename)

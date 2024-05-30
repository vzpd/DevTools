class AppException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

    def get_msg(self):
        return self.msg

    def get_code(self):
        return self.code

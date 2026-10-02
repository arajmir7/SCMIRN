"""SMS service placeholder."""

class SMSService:
    def __init__(self, provider=None):
        self.provider = provider

    def send(self, to, message):
        raise NotImplementedError('SMS service not configured')

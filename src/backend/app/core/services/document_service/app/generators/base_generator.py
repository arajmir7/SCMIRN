"""
Base document generator interface.
Concrete generators must implement `generate(data)` and return a string payload.
"""


class BaseGenerator:
    def generate(self, data):
        raise NotImplementedError("Subclasses must implement generate(data).")

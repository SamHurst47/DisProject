from app.base_module import InputModule

class TextInputModule(InputModule):
    """
    Simple input module that returns a fixed string.
    """

    def __init__(self, text):
        self.text = text

    def read(self):
        return self.text
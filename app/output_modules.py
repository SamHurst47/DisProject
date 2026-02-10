from app.base_module import OutputModule

class PrintOutputModule(OutputModule):
    """
    Output module that prints final pipeline result.
    """

    def write(self, data):
        print(data)

class Pipeline:
    def __init__(self, input_module, output_module):
        self.input_module = input_module
        self.output_module = output_module
        self.middle_modules = []

    def add_module(self, module):
        self.middle_modules.append(module)

    def run(self):
        data = self.input_module.process()
        for module in self.middle_modules:
            data = module.process(data)
        self.output_module.process(data)

from app.base_module import PipelineModule

class Static1(PipelineModule):
    """
    Placeholder static analysis module.
    """

    def process(self, data):
        return "data" + '!'

# app/base_module.py

from abc import ABC, abstractmethod


class PipelineModule(ABC):
    """
    Base class for all pipeline modules.
    """

    @abstractmethod
    def process(self, data):
        pass


class InputModule(PipelineModule):
    """
    Base class for input modules.
    """

    @abstractmethod
    def read(self):
        pass

    def process(self, data=None):
        return self.read()


class OutputModule(PipelineModule):
    """
    Base class for output modules.
    """

    @abstractmethod
    def write(self, data):
        pass

    def process(self, data):
        self.write(data)
        return data

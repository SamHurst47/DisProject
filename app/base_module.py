from abc import ABC, abstractmethod

class PipelineModule(ABC):
    """
    Base class for all pipeline modules.
    Every module in the pipeline must be able to process data.
    """
    @abstractmethod
    def process(self, data):
        pass


class InputModule(PipelineModule):
    """
    Base class for input modules (e.g., File upload, Text paste, Webhook).
    """

    @abstractmethod
    def read(self):
        """Reads the source and returns a CodeReviewPayload."""
        pass

    def process(self, data=None):
        # Input modules usually start the chain, so data might be None initially
        return self.read()


class AnalyzerModule(PipelineModule):
    """
    Base class for analysis modules (e.g., LLM Reviewers, Static Linters).
    Takes a payload, analyzes it, and appends/returns results.
    """

    @abstractmethod
    def analyze(self, data):
        """Performs the actual analysis logic."""
        pass

    def process(self, data):
        # Takes the data (CodeReviewPayload), runs analysis, and passes it forward
        return self.analyze(data)


class OutputModule(PipelineModule):
    """
    Base class for output modules (e.g., returning JSON to the web app, 
    writing to a DB, or posting a PR comment).
    """

    @abstractmethod
    def write(self, data):
        """Handles the final output of the processed data."""
        pass

    def process(self, data):
        self.write(data)
        return data
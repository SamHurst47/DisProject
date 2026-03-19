"""
input_modules.py

Used to define the different input methods utilising payload define in code_review_payload
and convert input in to payload format enabling dynamic pipeline execution.

Author: Sam Hurst
"""

from app.base_module import InputModule
from app.code_review_payload import CodeReviewPayload

class TextInputModule(InputModule):
    """
    Handles raw text inputs for easy access and upload.
    """
    def __init__(self, text: str, filename: str = "snippet.py", language: str = "python"):
        self.text = text
        self.filename = filename
        self.language = language

    def read(self) -> CodeReviewPayload:
        # could add simple validation
        return CodeReviewPayload(
            raw_content=self.text,
            filename=self.filename,
            language=self.language,
            is_diff=False
        )


class FileUploadInputModule(InputModule):
    """
    Handles files uploaded through the web app. 
    """
    def __init__(self, file_content: str, filename: str):
        self.file_content = file_content
        self.filename = filename
        self.language = "python" # enables future adaptability 

    def read(self) -> CodeReviewPayload:
        return CodeReviewPayload(
            raw_content=self.file_content,
            filename=self.filename,
            language=self.language,
            is_diff=False
        )


class WebhookDiffInputModule(InputModule):
    """
    Handles upload of git PR and other upload of whole projects.
    """
    def __init__(self, diff_text: str, pr_author: str):
        self.diff_text = diff_text
        self.author = pr_author

    def read(self) -> CodeReviewPayload:
        return CodeReviewPayload(
            raw_content=self.diff_text,
            filename="PR_Diff", # Or parse the diff to get filenames
            language="diff",
            is_diff=True,
            author=self.author
        )
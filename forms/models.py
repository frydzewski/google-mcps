"""Data models for Google Forms API."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class Question:
    """A question in a form."""
    question_id: str
    title: str
    description: Optional[str]
    required: bool
    question_type: str  # TEXT, PARAGRAPH, CHOICE, CHECKBOX, DROPDOWN, SCALE, DATE, TIME, FILE_UPLOAD, GRID
    options: list[str] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, item: dict) -> Optional["Question"]:
        """Parse from Forms API item response."""
        # Items can be questions, page breaks, images, etc.
        # Only process question items
        question_item = item.get("questionItem")
        if not question_item:
            return None

        question = question_item.get("question", {})
        question_id = question.get("questionId", "")

        # Get question type and options
        question_type, options = cls._parse_question_type(question)

        return cls(
            question_id=question_id,
            title=item.get("title", ""),
            description=item.get("description"),
            required=question.get("required", False),
            question_type=question_type,
            options=options,
        )

    @staticmethod
    def _parse_question_type(question: dict) -> tuple[str, list[str]]:
        """Determine question type and extract options."""
        options = []

        if "textQuestion" in question:
            text_q = question["textQuestion"]
            if text_q.get("paragraph", False):
                return "PARAGRAPH", []
            return "TEXT", []

        if "choiceQuestion" in question:
            choice_q = question["choiceQuestion"]
            choice_type = choice_q.get("type", "RADIO")
            options = [opt.get("value", "") for opt in choice_q.get("options", [])]

            if choice_type == "CHECKBOX":
                return "CHECKBOX", options
            elif choice_type == "DROP_DOWN":
                return "DROPDOWN", options
            return "CHOICE", options

        if "scaleQuestion" in question:
            scale_q = question["scaleQuestion"]
            low = scale_q.get("low", 1)
            high = scale_q.get("high", 5)
            return "SCALE", [f"{low}-{high}"]

        if "dateQuestion" in question:
            return "DATE", []

        if "timeQuestion" in question:
            return "TIME", []

        if "fileUploadQuestion" in question:
            return "FILE_UPLOAD", []

        if "rowQuestion" in question:
            return "GRID", []

        return "UNKNOWN", []


@dataclass
class Form:
    """A Google Form."""
    form_id: str
    title: str
    description: Optional[str]
    document_title: str
    responder_uri: str
    questions: list[Question] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, data: dict) -> "Form":
        """Parse from Forms API response."""
        info = data.get("info", {})

        # Parse questions from items
        questions = []
        for item in data.get("items", []):
            question = Question.from_api_response(item)
            if question:
                questions.append(question)

        return cls(
            form_id=data.get("formId", ""),
            title=info.get("title", ""),
            description=info.get("description"),
            document_title=info.get("documentTitle", ""),
            responder_uri=data.get("responderUri", ""),
            questions=questions,
        )


@dataclass
class Answer:
    """An answer to a question."""
    question_id: str
    text_answers: list[str] = field(default_factory=list)
    file_upload_answers: list[str] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, question_id: str, data: dict) -> "Answer":
        """Parse from Forms API answer response."""
        text_answers = []
        file_answers = []

        # Text answers (includes choice selections)
        text_data = data.get("textAnswers", {})
        for answer in text_data.get("answers", []):
            value = answer.get("value", "")
            if value:
                text_answers.append(value)

        # File upload answers
        file_data = data.get("fileUploadAnswers", {})
        for answer in file_data.get("answers", []):
            file_id = answer.get("fileId", "")
            if file_id:
                file_answers.append(f"https://drive.google.com/file/d/{file_id}")

        return cls(
            question_id=question_id,
            text_answers=text_answers,
            file_upload_answers=file_answers,
        )


@dataclass
class FormResponse:
    """A response to a form."""
    response_id: str
    create_time: datetime
    last_submitted_time: datetime
    respondent_email: Optional[str]
    answers: dict[str, Answer] = field(default_factory=dict)

    @classmethod
    def from_api_response(cls, data: dict) -> "FormResponse":
        """Parse from Forms API response."""
        # Parse timestamps
        create_time = cls._parse_timestamp(data.get("createTime", ""))
        last_submitted = cls._parse_timestamp(data.get("lastSubmittedTime", ""))

        # Parse answers
        answers = {}
        for question_id, answer_data in data.get("answers", {}).items():
            answers[question_id] = Answer.from_api_response(question_id, answer_data)

        return cls(
            response_id=data.get("responseId", ""),
            create_time=create_time,
            last_submitted_time=last_submitted,
            respondent_email=data.get("respondentEmail"),
            answers=answers,
        )

    @staticmethod
    def _parse_timestamp(ts: str) -> datetime:
        """Parse ISO timestamp from API."""
        if not ts:
            return datetime.now()
        # Handle Z suffix
        if ts.endswith("Z"):
            ts = ts.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            return datetime.now()


@dataclass
class ResponseSummary:
    """Summary of form responses."""
    form_id: str
    total_responses: int
    responses: list[FormResponse] = field(default_factory=list)

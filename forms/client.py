"""Google Forms API client wrapper."""
from typing import Optional
import logging

from .models import Form, Question, FormResponse, Answer, ResponseSummary

logger = logging.getLogger("google_mcps.forms")


class FormsClient:
    """Wrapper for Google Forms API operations (read-only)."""

    def __init__(self, service):
        """
        Initialize the Forms client.

        Args:
            service: Google Forms API service object
        """
        self.service = service

    def get_form(self, form_id: str) -> Form:
        """
        Get form structure including all questions.

        Args:
            form_id: The form ID (from the Google Forms URL)

        Returns:
            Form object with title, description, and questions
        """
        try:
            result = self.service.forms().get(formId=form_id).execute()
        except Exception as e:
            logger.error(f"Failed to get form {form_id}: {e}")
            raise

        return Form.from_api_response(result)

    def list_responses(
        self,
        form_id: str,
        page_size: int = 100,
    ) -> ResponseSummary:
        """
        List all responses to a form.

        Args:
            form_id: The form ID
            page_size: Number of responses per page (max 5000)

        Returns:
            ResponseSummary with total count and list of responses
        """
        responses = []
        page_token = None

        while True:
            try:
                request = self.service.forms().responses().list(
                    formId=form_id,
                    pageSize=min(page_size, 5000),
                )
                if page_token:
                    request = self.service.forms().responses().list(
                        formId=form_id,
                        pageSize=min(page_size, 5000),
                        pageToken=page_token,
                    )

                result = request.execute()
            except Exception as e:
                logger.error(f"Failed to list responses for {form_id}: {e}")
                raise

            for response_data in result.get("responses", []):
                responses.append(FormResponse.from_api_response(response_data))

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        return ResponseSummary(
            form_id=form_id,
            total_responses=len(responses),
            responses=responses,
        )

    def get_response(self, form_id: str, response_id: str) -> FormResponse:
        """
        Get a specific response by ID.

        Args:
            form_id: The form ID
            response_id: The response ID

        Returns:
            FormResponse object
        """
        try:
            result = (
                self.service.forms()
                .responses()
                .get(formId=form_id, responseId=response_id)
                .execute()
            )
        except Exception as e:
            logger.error(f"Failed to get response {response_id}: {e}")
            raise

        return FormResponse.from_api_response(result)

    def get_responses_as_rows(self, form_id: str, limit: int = 100) -> list[dict]:
        """
        Get responses in a tabular format.

        Returns list of dicts where keys are question titles
        and values are the answers. Useful for analysis or export.

        Args:
            form_id: The form ID
            limit: Maximum number of responses to return

        Returns:
            List of row dicts with question titles as keys
        """
        # Get form to map question IDs to titles
        form = self.get_form(form_id)
        question_map = {q.question_id: q.title for q in form.questions}

        # Get responses
        summary = self.list_responses(form_id, page_size=limit)

        rows = []
        for response in summary.responses[:limit]:
            row = {
                "_response_id": response.response_id,
                "_submitted_at": response.last_submitted_time.isoformat(),
                "_email": response.respondent_email or "",
            }

            for question_id, answer in response.answers.items():
                title = question_map.get(question_id, question_id)
                # Combine text answers into single string
                if answer.text_answers:
                    row[title] = ", ".join(answer.text_answers)
                elif answer.file_upload_answers:
                    row[title] = ", ".join(answer.file_upload_answers)
                else:
                    row[title] = ""

            rows.append(row)

        return rows

    def get_question_titles(self, form_id: str) -> list[str]:
        """
        Get list of question titles from a form.

        Args:
            form_id: The form ID

        Returns:
            List of question titles in order
        """
        form = self.get_form(form_id)
        return [q.title for q in form.questions]

    def get_response_summary(self, form_id: str) -> dict:
        """
        Generate summary statistics for form responses.

        Args:
            form_id: The form ID

        Returns:
            Summary dict with:
            - total_responses: int
            - first_response: datetime ISO string or None
            - last_response: datetime ISO string or None
            - question_stats: dict mapping question title to answer stats
        """
        # Get form structure for question titles and types
        form = self.get_form(form_id)
        question_map = {q.question_id: q for q in form.questions}

        # Get all responses
        summary = self.list_responses(form_id)

        if summary.total_responses == 0:
            return {
                "total_responses": 0,
                "first_response": None,
                "last_response": None,
                "question_stats": {},
            }

        # Calculate date range
        timestamps = [r.last_submitted_time for r in summary.responses]
        first_response = min(timestamps)
        last_response = max(timestamps)

        # Calculate question stats
        question_stats = {}
        for question in form.questions:
            qid = question.question_id
            title = question.title
            qtype = question.question_type

            # Count answers for this question
            answers = []
            for response in summary.responses:
                if qid in response.answers:
                    answer = response.answers[qid]
                    answers.extend(answer.text_answers)

            if qtype in ("CHOICE", "CHECKBOX", "DROPDOWN"):
                # Distribution for choice questions
                distribution = {}
                for answer_val in answers:
                    distribution[answer_val] = distribution.get(answer_val, 0) + 1
                question_stats[title] = {
                    "type": qtype,
                    "total_answers": len(answers),
                    "distribution": distribution,
                }
            else:
                # Just count for text/other questions
                question_stats[title] = {
                    "type": qtype,
                    "total_answers": len(answers),
                }

        return {
            "total_responses": summary.total_responses,
            "first_response": first_response.isoformat(),
            "last_response": last_response.isoformat(),
            "question_stats": question_stats,
        }

    def get_answer_distribution(
        self,
        form_id: str,
        question_id: str,
    ) -> dict[str, int]:
        """
        Get answer distribution for a specific question.

        Useful for choice-based questions to see how responses are distributed.

        Args:
            form_id: The form ID
            question_id: The question ID

        Returns:
            Dict mapping answer value to count
        """
        summary = self.list_responses(form_id)

        distribution: dict[str, int] = {}
        for response in summary.responses:
            if question_id in response.answers:
                answer = response.answers[question_id]
                for answer_val in answer.text_answers:
                    distribution[answer_val] = distribution.get(answer_val, 0) + 1

        return distribution

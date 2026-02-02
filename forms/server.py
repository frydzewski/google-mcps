"""Forms MCP Server - Google Forms operations via Model Context Protocol."""
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP
from googleapiclient.discovery import build

from shared.auth import GoogleAuth, FORMS_SCOPES
from shared.paths import MCPPaths, ensure_data_dirs
from .client import FormsClient

# Initialize the MCP server
mcp = FastMCP("forms")

# App name can be overridden via environment
APP_NAME = os.environ.get("GOOGLE_MCP_APP_NAME", "letter-rip")

# Cached instances
_paths: Optional[MCPPaths] = None
_forms_client: Optional[FormsClient] = None


def get_paths() -> MCPPaths:
    """Get or create paths instance."""
    global _paths
    if _paths is None:
        _paths = MCPPaths(APP_NAME)
        ensure_data_dirs(_paths.data_dir)
    return _paths


def get_forms_client() -> FormsClient:
    """Get or create authenticated Forms client."""
    global _forms_client

    if _forms_client is not None:
        return _forms_client

    paths = get_paths()

    if not paths.forms_token.exists():
        raise RuntimeError(
            f"Forms not authenticated. Token not found at: {paths.forms_token}\n"
            "Run: python -m forms.auth"
        )

    auth = GoogleAuth(
        credentials_path=paths.forms_credentials,
        token_path=paths.forms_token,
        scopes=FORMS_SCOPES,
    )

    creds = auth.get_credentials()
    service = build("forms", "v1", credentials=creds)
    client = FormsClient(service=service)

    _forms_client = client
    return _forms_client


# =============================================================================
# FORMS READ OPERATIONS (6 tools)
# =============================================================================


@mcp.tool()
def get_form(form_id: str) -> dict:
    """
    Get form structure including title, description, and all questions.

    Args:
        form_id: The form ID (from the Google Forms URL after /d/)

    Returns:
        Form metadata with title, description, responder_uri, and list of questions.
        Each question has id, title, type, required flag, and options (for choice questions).
    """
    client = get_forms_client()
    form = client.get_form(form_id)

    return {
        "form_id": form.form_id,
        "title": form.title,
        "description": form.description,
        "document_title": form.document_title,
        "responder_uri": form.responder_uri,
        "questions": [
            {
                "question_id": q.question_id,
                "title": q.title,
                "description": q.description,
                "required": q.required,
                "question_type": q.question_type,
                "options": q.options,
            }
            for q in form.questions
        ],
    }


@mcp.tool()
def list_questions(form_id: str) -> list[dict]:
    """
    List all questions in a form.

    A simpler view than get_form, returning just the questions.

    Args:
        form_id: The form ID

    Returns:
        List of questions with id, title, type, required flag, and options.
    """
    client = get_forms_client()
    form = client.get_form(form_id)

    return [
        {
            "question_id": q.question_id,
            "title": q.title,
            "question_type": q.question_type,
            "required": q.required,
            "options": q.options,
        }
        for q in form.questions
    ]


@mcp.tool()
def get_responses(
    form_id: str,
    limit: int = 100,
) -> dict:
    """
    Get all responses to a form.

    Args:
        form_id: The form ID
        limit: Maximum number of responses to return (default 100)

    Returns:
        Summary with total_responses count and list of responses.
        Each response includes response_id, submitted_at, email, and answers.
    """
    client = get_forms_client()
    summary = client.list_responses(form_id, page_size=limit)

    return {
        "form_id": summary.form_id,
        "total_responses": summary.total_responses,
        "responses": [
            {
                "response_id": r.response_id,
                "submitted_at": r.last_submitted_time.isoformat(),
                "email": r.respondent_email,
                "answers": {
                    qid: {
                        "text_answers": a.text_answers,
                        "file_upload_answers": a.file_upload_answers,
                    }
                    for qid, a in r.answers.items()
                },
            }
            for r in summary.responses[:limit]
        ],
    }


@mcp.tool()
def get_responses_table(form_id: str, limit: int = 100) -> list[dict]:
    """
    Get responses in tabular format for easy analysis or export.

    Returns data with question titles as keys (instead of question IDs),
    making it easy to read and export to sheets.

    Args:
        form_id: The form ID
        limit: Maximum number of responses to return (default 100)

    Returns:
        List of response rows. Each row is a dict with:
        - _response_id: The response ID
        - _submitted_at: Submission timestamp
        - _email: Respondent email (if collected)
        - [question_title]: Answer value for each question
    """
    client = get_forms_client()
    return client.get_responses_as_rows(form_id, limit=limit)


@mcp.tool()
def get_response(form_id: str, response_id: str) -> dict:
    """
    Get a specific response by ID.

    Args:
        form_id: The form ID
        response_id: The response ID

    Returns:
        Response with response_id, submitted_at, email, and answers.
    """
    client = get_forms_client()
    response = client.get_response(form_id, response_id)

    return {
        "response_id": response.response_id,
        "submitted_at": response.last_submitted_time.isoformat(),
        "email": response.respondent_email,
        "answers": {
            qid: {
                "text_answers": a.text_answers,
                "file_upload_answers": a.file_upload_answers,
            }
            for qid, a in response.answers.items()
        },
    }


@mcp.tool()
def get_response_summary(form_id: str) -> dict:
    """
    Get summary statistics for form responses.

    Provides an overview of response activity and answer distributions
    for choice-based questions.

    Args:
        form_id: The form ID

    Returns:
        Summary with:
        - total_responses: Total number of responses
        - first_response: Timestamp of earliest response
        - last_response: Timestamp of most recent response
        - question_stats: Dict mapping question titles to answer counts/distributions
    """
    client = get_forms_client()
    return client.get_response_summary(form_id)

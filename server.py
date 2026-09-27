import os
import requests

from dotenv import load_dotenv
from mcp.server import MCPServer


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------

load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")


# --------------------------------------------------
# Validate configuration
# --------------------------------------------------

if not JIRA_URL:
    raise ValueError("JIRA_URL is missing in .env")

if not JIRA_EMAIL:
    raise ValueError("JIRA_EMAIL is missing in .env")

if not JIRA_API_TOKEN:
    raise ValueError("JIRA_API_TOKEN is missing in .env")

if not JIRA_PROJECT_KEY:
    raise ValueError("JIRA_PROJECT_KEY is missing in .env")


# --------------------------------------------------
# Create MCP server
# --------------------------------------------------

mcp = MCPServer(
    "Jira User Stories"
)


# --------------------------------------------------
# Jira GET helper
# --------------------------------------------------

def jira_get(endpoint, params=None):

    url = f"{JIRA_URL}{endpoint}"

    response = requests.get(
        url,
        params=params,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={
            "Accept": "application/json"
        },
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(
            f"Jira API error {response.status_code}: "
            f"{response.text}"
        )

    return response.json()


# --------------------------------------------------
# Tool 1 - Get Jira Project
# --------------------------------------------------

@mcp.tool()
def get_jira_project():
    """
    Get information about the configured Jira project.
    """

    data = jira_get(
        f"/rest/api/3/project/{JIRA_PROJECT_KEY}"
    )

    return {
        "key": data.get("key"),
        "name": data.get("name"),
        "description": data.get("description"),
        "url": f"{JIRA_URL}/browse/{JIRA_PROJECT_KEY}"
    }


# --------------------------------------------------
# Tool 2 - Get User Stories
# --------------------------------------------------

@mcp.tool()
def get_user_stories():
    """
    Fetch user stories from the configured Jira project.
    """

    jql = (
        f'project = "{JIRA_PROJECT_KEY}" '
        f'AND issuetype = Story '
        f'ORDER BY created DESC'
    )

    data = jira_get(
        "/rest/api/3/search/jql",
        params={
            "jql": jql,
            "maxResults": 50,
            "fields": "summary,status,priority,assignee"
        }
    )

    stories = []

    for issue in data.get("issues", []):

        fields = issue.get("fields", {})

        status = fields.get("status")
        priority = fields.get("priority")
        assignee = fields.get("assignee")

        stories.append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),

            "status": (
                status.get("name")
                if status
                else None
            ),

            "priority": (
                priority.get("name")
                if priority
                else None
            ),

            "assignee": (
                assignee.get("displayName")
                if assignee
                else None
            ),

            "url": (
                f"{JIRA_URL}/browse/{issue.get('key')}"
            )
        })

    return stories


# --------------------------------------------------
# Tool 3 - Get Specific User Story
# --------------------------------------------------

@mcp.tool()
def get_user_story(issue_key: str):
    """
    Get details of a specific Jira user story.

    Example:
    AVD-1
    """

    data = jira_get(
        f"/rest/api/3/issue/{issue_key}",
        params={
            "fields": (
                "summary,status,description,"
                "priority,assignee,issuetype"
            )
        }
    )

    fields = data.get("fields", {})

    status = fields.get("status")
    priority = fields.get("priority")
    assignee = fields.get("assignee")
    issuetype = fields.get("issuetype")

    return {
        "key": data.get("key"),

        "summary": fields.get("summary"),

        "issue_type": (
            issuetype.get("name")
            if issuetype
            else None
        ),

        "status": (
            status.get("name")
            if status
            else None
        ),

        "priority": (
            priority.get("name")
            if priority
            else None
        ),

        "assignee": (
            assignee.get("displayName")
            if assignee
            else None
        ),

        "url": (
            f"{JIRA_URL}/browse/{data.get('key')}"
        )
    }


# --------------------------------------------------
# Tool 4 - Search Jira using JQL
# --------------------------------------------------

@mcp.tool()
def search_jira(jql: str):
    """
    Search Jira issues using JQL.

    Example:

    project = AVD AND status = "To Do"
    """

    data = jira_get(
        "/rest/api/3/search/jql",
        params={
            "jql": jql,
            "maxResults": 50,
            "fields": (
                "summary,status,issuetype,"
                "priority,assignee"
            )
        }
    )

    results = []

    for issue in data.get("issues", []):

        fields = issue.get("fields", {})

        status = fields.get("status")
        issuetype = fields.get("issuetype")

        results.append({
            "key": issue.get("key"),

            "summary": fields.get("summary"),

            "issue_type": (
                issuetype.get("name")
                if issuetype
                else None
            ),

            "status": (
                status.get("name")
                if status
                else None
            ),

            "url": (
                f"{JIRA_URL}/browse/{issue.get('key')}"
            )
        })

    return results


# --------------------------------------------------
# Start MCP server
# --------------------------------------------------

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8000))

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port
    )
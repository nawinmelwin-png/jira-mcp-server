import os
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")


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
            f"Jira API error {response.status_code}: {response.text}"
        )

    return response.json()


def get_project():

    data = jira_get(
        f"/rest/api/3/project/{JIRA_PROJECT_KEY}"
    )

    return {
        "key": data.get("key"),
        "name": data.get("name"),
        "description": data.get("description"),
        "url": f"{JIRA_URL}/browse/{JIRA_PROJECT_KEY}"
    }


def get_user_stories():

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
            "fields": "summary,description,status,priority,assignee"
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
            "description": fields.get("description"),
            "status": status.get("name") if status else None,
            "priority": priority.get("name") if priority else None,
            "assignee": (
                assignee.get("displayName")
                if assignee else None
            ),
            "url": f"{JIRA_URL}/browse/{issue.get('key')}"
        })

    return stories


def get_user_story(issue_key):

    data = jira_get(
        f"/rest/api/3/issue/{issue_key}",
        params={
            "fields": (
                "summary,"
                "description,"
                "status,"
                "priority,"
                "assignee,"
                "issuetype"
            )
        }
    )

    fields = data.get("fields", {})

    status = fields.get("status")
    priority = fields.get("priority")
    assignee = fields.get("assignee")
    issue_type = fields.get("issuetype")

    return {
        "key": data.get("key"),
        "summary": fields.get("summary"),
        "description": fields.get("description"),
        "issue_type": (
            issue_type.get("name")
            if issue_type else None
        ),
        "status": (
            status.get("name")
            if status else None
        ),
        "priority": (
            priority.get("name")
            if priority else None
        ),
        "assignee": (
            assignee.get("displayName")
            if assignee else None
        ),
        "url": f"{JIRA_URL}/browse/{data.get('key')}"
    }


def search_jira(jql):

    data = jira_get(
        "/rest/api/3/search/jql",
        params={
            "jql": jql,
            "maxResults": 50,
            "fields": (
                "summary,"
                "description,"
                "status,"
                "issuetype,"
                "priority,"
                "assignee"
            )
        }
    )

    results = []

    for issue in data.get("issues", []):

        fields = issue.get("fields", {})

        status = fields.get("status")
        issue_type = fields.get("issuetype")

        results.append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "description": fields.get("description"),
            "issue_type": (
                issue_type.get("name")
                if issue_type else None
            ),
            "status": (
                status.get("name")
                if status else None
            ),
            "url": f"{JIRA_URL}/browse/{issue.get('key')}"
        })

    return results
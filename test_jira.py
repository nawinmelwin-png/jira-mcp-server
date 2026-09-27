import os
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY")

url = f"{JIRA_URL}/rest/api/3/search/jql"

params = {
    "jql": f'project = "{JIRA_PROJECT_KEY}" ORDER BY created DESC',
    "maxResults": 20,
    "fields": "summary,status,issuetype"
}

response = requests.get(
    url,
    params=params,
    auth=(JIRA_EMAIL, JIRA_API_TOKEN),
    headers={
        "Accept": "application/json"
    }
)

print("Status:", response.status_code)

if response.status_code != 200:
    print(response.text)
    exit()

data = response.json()

print("\nJira User Stories:\n")

for issue in data.get("issues", []):
    fields = issue["fields"]

    print(
        f'{issue["key"]} | '
        f'{fields["issuetype"]["name"]} | '
        f'{fields["status"]["name"]} | '
        f'{fields["summary"]}'
    )
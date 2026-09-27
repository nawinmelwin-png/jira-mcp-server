import os
import base64
import time
import requests

from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

GITHUB_API = "https://api.github.com"


if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is missing")

if not GITHUB_USERNAME:
    raise ValueError("GITHUB_USERNAME is missing")


def github_headers():
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2026-03-10"
    }


def create_repository(
    repository_name,
    description="AI Generated Selenium Java Automation",
    private=True
):
    """
    Create a new GitHub repository.
    """

    response = requests.post(
        f"{GITHUB_API}/user/repos",
        headers=github_headers(),
        json={
            "name": repository_name,
            "description": description,
            "private": private,
            "has_issues": True,
            "has_projects": False,
            "has_wiki": False
        },
        timeout=30
    )

    if response.status_code != 201:
        raise Exception(
            f"GitHub repository creation failed "
            f"{response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    return {
        "name": data["name"],
        "url": data["html_url"],
        "clone_url": data["clone_url"],
        "default_branch": data["default_branch"]
    }


def upload_file(
    repository_name,
    file_path,
    content,
    commit_message
):
    """
    Upload one file to a GitHub repository.
    """

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    url = (
        f"{GITHUB_API}/repos/"
        f"{GITHUB_USERNAME}/"
        f"{repository_name}/"
        f"contents/{file_path}"
    )

    for attempt in range(3):

        response = requests.put(
            url,
            headers=github_headers(),
            json={
                "message": commit_message,
                "content": encoded_content
            },
            timeout=30
        )

        if response.status_code in (200, 201):
            break

        # Repository may still be initializing
        if response.status_code == 409:
            time.sleep(2)
            continue

        raise Exception(
            f"GitHub file upload failed "
            f"{response.status_code}: "
            f"{response.text}"
        )

    else:
        raise Exception(
            "GitHub repository is not ready "
            "for file upload."
        )

    data = response.json()

    return {
        "path": file_path,
        "url": data["content"]["html_url"]
    }


def upload_files(repository_name, files):
    """
    Upload all generated automation files.
    """

    uploaded = []

    for file in files:

        result = upload_file(
            repository_name=repository_name,
            file_path=file["path"],
            content=file["content"],
            commit_message=(
                f"Add automation file: "
                f"{file['path']}"
            )
        )

        uploaded.append(result)

    return uploaded
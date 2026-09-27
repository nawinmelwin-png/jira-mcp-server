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
    description="AI Generated Selenium Java Automation Tests",
    private=True
):
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
        "default_branch": data.get("default_branch")
    }


def wait_for_repository(repository_name, attempts=10):
    """
    Wait until GitHub has finished creating the repository.
    """

    url = (
        f"{GITHUB_API}/repos/"
        f"{GITHUB_USERNAME}/"
        f"{repository_name}"
    )

    for attempt in range(attempts):

        response = requests.get(
            url,
            headers=github_headers(),
            timeout=30
        )

        if response.status_code == 200:
            return response.json()

        print(
            f"Waiting for GitHub repository "
            f"({attempt + 1}/{attempts})..."
        )

        time.sleep(2)

    raise Exception(
        "GitHub repository was created but "
        "is not ready yet."
    )


def upload_file(
    repository_name,
    file_path,
    content,
    commit_message
):

    # --------------------------------------------------
    # Wait for repository creation to finish
    # --------------------------------------------------

    repository = wait_for_repository(
        repository_name
    )

    default_branch = repository.get(
        "default_branch"
    )

    # Empty repositories may not have a branch yet.
    # In that case GitHub will initialize the repository
    # when the first file is created.

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    url = (
        f"{GITHUB_API}/repos/"
        f"{GITHUB_USERNAME}/"
        f"{repository_name}/"
        f"contents/"
        f"{file_path}"
    )

    payload = {
        "message": commit_message,
        "content": encoded_content
    }

    # Only specify branch when GitHub already has one.
    if default_branch:
        payload["branch"] = default_branch

    for attempt in range(5):

        response = requests.put(
            url,
            headers=github_headers(),
            json=payload,
            timeout=30
        )

        if response.status_code in (200, 201):

            data = response.json()

            return {
                "path": file_path,
                "url": data["content"]["html_url"],
                "commit": data["commit"]["sha"]
            }

        # GitHub can temporarily return 409 immediately
        # after repository creation.
        if response.status_code == 409:

            print(
                f"GitHub returned 409 for {file_path}. "
                f"Retrying ({attempt + 1}/5)..."
            )

            time.sleep(3)
            continue

        # Authentication / permission
        if response.status_code == 403:
            raise Exception(
                f"GitHub upload permission denied "
                f"403: {response.text}"
            )

        # Repository/path doesn't exist
        if response.status_code == 404:
            raise Exception(
                f"GitHub repository/path not found "
                f"404: {response.text}"
            )

        # Validation error
        if response.status_code == 422:
            raise Exception(
                f"GitHub upload validation failed "
                f"422: {response.text}"
            )

        raise Exception(
            f"GitHub file upload failed "
            f"{response.status_code}: "
            f"{response.text}"
        )

    raise Exception(
        f"GitHub upload failed after 5 attempts "
        f"for file: {file_path}"
    )


def upload_files(repository_name, files):

    uploaded = []

    for index, file in enumerate(files, start=1):

        print(
            f"Uploading {index}/{len(files)}: "
            f"{file['path']}"
        )

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
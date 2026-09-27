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


def get_repository(repository_name):
    url = (
        f"{GITHUB_API}/repos/"
        f"{GITHUB_USERNAME}/"
        f"{repository_name}"
    )

    response = requests.get(
        url,
        headers=github_headers(),
        timeout=30
    )

    if response.status_code == 200:
        return response.json()

    if response.status_code == 404:
        return None

    raise Exception(
        f"GitHub repository lookup failed "
        f"{response.status_code}: "
        f"{response.text}"
    )


def create_repository(
    repository_name,
    description="AI Generated Selenium Java Automation Tests",
    private=True
):
    # IMPORTANT:
    # Reuse repository if it already exists.
    existing = get_repository(repository_name)

    if existing:
        print(
            f"GitHub repository already exists: "
            f"{repository_name}"
        )

        return {
            "name": existing["name"],
            "url": existing["html_url"],
            "clone_url": existing["clone_url"],
            "default_branch": existing.get("default_branch")
        }

    print(
        f"Creating GitHub repository: "
        f"{repository_name}"
    )

    response = requests.post(
        f"{GITHUB_API}/user/repos",
        headers=github_headers(),
        json={
            "name": repository_name,
            "description": description,
            "private": private,
            "has_issues": True,
            "has_projects": False,
            "has_wiki": False,
            "auto_init": True
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

    print(
        f"GitHub repository created: "
        f"{data['html_url']}"
    )

    return {
        "name": data["name"],
        "url": data["html_url"],
        "clone_url": data["clone_url"],
        "default_branch": data.get("default_branch")
    }


def upload_file(
    repository_name,
    file_path,
    content,
    commit_message
):
    repository = get_repository(repository_name)

    if not repository:
        raise Exception(
            f"GitHub repository does not exist: "
            f"{repository_name}"
        )

    branch = repository.get("default_branch") or "main"

    url = (
        f"{GITHUB_API}/repos/"
        f"{GITHUB_USERNAME}/"
        f"{repository_name}/"
        f"contents/"
        f"{file_path}"
    )

    encoded_content = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": commit_message,
        "content": encoded_content,
        "branch": branch
    }

    # Check whether the file already exists.
    # If it exists, GitHub requires its SHA for update.
    existing_response = requests.get(
        url,
        headers=github_headers(),
        params={"ref": branch},
        timeout=30
    )

    if existing_response.status_code == 200:
        existing_file = existing_response.json()
        payload["sha"] = existing_file["sha"]

        print(
            f"Updating existing file: "
            f"{file_path}"
        )

    elif existing_response.status_code == 404:
        print(
            f"Creating file: "
            f"{file_path}"
        )

    else:
        raise Exception(
            f"GitHub file lookup failed "
            f"{existing_response.status_code}: "
            f"{existing_response.text}"
        )

    for attempt in range(5):

        response = requests.put(
            url,
            headers=github_headers(),
            json=payload,
            timeout=30
        )

        if response.status_code in (200, 201):

            data = response.json()

            print(
                f"Uploaded successfully: "
                f"{file_path}"
            )

            return {
                "path": file_path,
                "url": data["content"]["html_url"],
                "commit": data["commit"]["sha"]
            }

        if response.status_code == 409:

            print(
                f"GitHub returned 409 for "
                f"{file_path}. "
                f"Retrying {attempt + 1}/5..."
            )

            time.sleep(3)
            continue

        if response.status_code == 403:
            raise Exception(
                f"GitHub upload permission denied "
                f"403: {response.text}"
            )

        if response.status_code == 404:
            raise Exception(
                f"GitHub repository/path not found "
                f"404: {response.text}"
            )

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
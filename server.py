import os

from dotenv import load_dotenv
from mcp.server import MCPServer

from jira_client import (
    get_project,
    get_user_stories,
    get_user_story,
    search_jira
)

from gemini_generator import (
    generate_selenium_project
)

from github_client import (
    create_repository,
    upload_files
)


load_dotenv()

mcp = MCPServer(
    "Jira AI Test Automation MCP"
)


# =========================================================
# JIRA TOOLS
# =========================================================

@mcp.tool()
def mcp_get_jira_project():

    return get_project()


@mcp.tool()
def mcp_get_user_stories():

    return get_user_stories()


@mcp.tool()
def mcp_get_user_story(
    issue_key: str
):

    return get_user_story(issue_key)


@mcp.tool()
def mcp_search_jira(
    jql: str
):

    return search_jira(jql)


# =========================================================
# GEMINI TEST GENERATION
# =========================================================

@mcp.tool()
def generate_test_automation(
    issue_keys: list[str]
):

    stories = []

    for issue_key in issue_keys:

        story = get_user_story(issue_key)

        stories.append(story)

    files = generate_selenium_project(
        stories
    )

    return {
        "status": "success",
        "stories_processed": len(stories),
        "files_generated": len(files),
        "files": [
            file["path"]
            for file in files
        ],
        "project": files
    }


# =========================================================
# GITHUB
# =========================================================

@mcp.tool()
def create_test_repository(
    repository_name: str,
    description: str = (
        "AI Generated Selenium Java "
        "Automation Tests"
    ),
    private: bool = True
):

    repository = create_repository(
        repository_name=repository_name,
        description=description,
        private=private
    )

    return {
        "status": "success",
        "repository": repository
    }


# =========================================================
# COMPLETE PIPELINE
# =========================================================

@mcp.tool()
def generate_and_publish_tests(
    issue_keys: list[str],
    repository_name: str,
    private: bool = True
):

    # -----------------------------------------------------
    # 1. Get Jira stories
    # -----------------------------------------------------

    stories = []

    for issue_key in issue_keys:

        story = get_user_story(
            issue_key
        )

        stories.append(story)

    if not stories:

        raise Exception(
            "No Jira stories found."
        )

    # -----------------------------------------------------
    # 2. Generate Selenium Java using Gemini
    # -----------------------------------------------------

    files = generate_selenium_project(
        stories
    )

    if not files:

        raise Exception(
            "Gemini did not generate any files."
        )

    # -----------------------------------------------------
    # 3. Create GitHub repository
    # -----------------------------------------------------

    repository = create_repository(
        repository_name=repository_name,
        description=(
            "AI generated Selenium Java "
            "automation for Jira stories"
        ),
        private=private
    )

    # -----------------------------------------------------
    # 4. Upload generated files
    # -----------------------------------------------------

    uploaded_files = upload_files(
        repository_name=repository_name,
        files=files
    )

    # -----------------------------------------------------
    # 5. Return result
    # -----------------------------------------------------

    return {
        "status": "success",

        "stories_processed": len(stories),

        "story_keys": [
            story["key"]
            for story in stories
        ],

        "files_generated": len(files),

        "repository": {
            "name": repository["name"],
            "url": repository["url"],
            "clone_url": repository["clone_url"]
        },

        "uploaded_files": uploaded_files
    }


# =========================================================
# SERVER
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            8000
        )
    )

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port
    )
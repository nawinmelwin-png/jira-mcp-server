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

        story = get_user_story(
            issue_key
        )

        if not story:
            raise Exception(
                f"Jira story not found: {issue_key}"
            )

        stories.append(story)

    if not stories:

        raise Exception(
            "No Jira stories found."
        )

    print(
        f"Generating automation for "
        f"{len(stories)} Jira stories..."
    )

    files = generate_selenium_project(
        stories
    )

    if not files:

        raise Exception(
            "Gemini did not generate any files."
        )

    print(
        f"Gemini generated "
        f"{len(files)} files."
    )

    return {
        "status": "success",

        "stories_processed": len(stories),

        "story_keys": [
            story["key"]
            for story in stories
        ],

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

    print(
        f"Checking GitHub repository: "
        f"{repository_name}"
    )

    # create_repository() now:
    #
    # 1. Checks whether the repository exists
    # 2. Reuses it if it already exists
    # 3. Creates it if it does not exist

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

    print("")
    print("========================================")
    print("GENERATE AND PUBLISH TESTS")
    print("========================================")

    print(
        f"Issue keys: {issue_keys}"
    )

    print(
        f"Repository: {repository_name}"
    )

    # -----------------------------------------------------
    # 1. GET JIRA STORIES
    # -----------------------------------------------------

    print("")
    print("STEP 1: Loading Jira stories...")

    stories = []

    for issue_key in issue_keys:

        print(
            f"Loading Jira story: {issue_key}"
        )

        story = get_user_story(
            issue_key
        )

        if not story:

            raise Exception(
                f"Jira story not found: "
                f"{issue_key}"
            )

        stories.append(story)

    if not stories:

        raise Exception(
            "No Jira stories found."
        )

    print(
        f"Stories loaded: "
        f"{len(stories)}"
    )

    # -----------------------------------------------------
    # 2. GENERATE SELENIUM JAVA USING GEMINI
    # -----------------------------------------------------

    print("")
    print(
        "STEP 2: Generating Selenium "
        "Java automation..."
    )

    files = generate_selenium_project(
        stories
    )

    if not files:

        raise Exception(
            "Gemini did not generate any files."
        )

    print(
        f"Gemini generated "
        f"{len(files)} files."
    )

    for file in files:

        print(
            f"  Generated: "
            f"{file['path']}"
        )

    # -----------------------------------------------------
    # 3. CREATE OR REUSE GITHUB REPOSITORY
    # -----------------------------------------------------

    print("")
    print(
        "STEP 3: Checking GitHub repository..."
    )

    repository = create_repository(
        repository_name=repository_name,
        description=(
            "AI generated Selenium Java "
            "automation for Jira stories"
        ),
        private=private
    )

    print(
        f"Repository ready: "
        f"{repository['url']}"
    )

    # -----------------------------------------------------
    # 4. UPLOAD GENERATED FILES
    # -----------------------------------------------------

    print("")
    print(
        "STEP 4: Uploading generated files..."
    )

    uploaded_files = upload_files(
        repository_name=repository_name,
        files=files
    )

    print("")
    print(
        f"Successfully uploaded "
        f"{len(uploaded_files)} files."
    )

    # -----------------------------------------------------
    # 5. RETURN RESULT
    # -----------------------------------------------------

    print("")
    print("========================================")
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("========================================")

    return {
        "status": "success",

        "message": (
            "Selenium automation generated "
            "and published successfully."
        ),

        "stories_processed": len(stories),

        "story_keys": [
            story["key"]
            for story in stories
        ],

        "files_generated": len(files),

        "files_uploaded": len(uploaded_files),

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

    print("")
    print("========================================")
    print("JIRA AI TEST AUTOMATION MCP")
    print("========================================")
    print(
        f"Starting MCP server on port {port}..."
    )
    print(
        f"MCP endpoint: "
        f"http://127.0.0.1:{port}/mcp"
    )
    print("========================================")
    print("")

    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port
    )
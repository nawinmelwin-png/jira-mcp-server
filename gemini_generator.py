import os
import json
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.6-flash"
)

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing")

client = genai.Client(
    api_key=GEMINI_API_KEY
)


SYSTEM_PROMPT = """
You are an expert Senior QA Automation Engineer.

You convert Jira user stories into production-quality
Selenium Java automation projects.

Technology requirements:

- Java
- Selenium WebDriver
- TestNG
- Maven
- Page Object Model
- WebDriverManager
- Clean reusable architecture
- Explicit waits
- Assertions
- Proper exception handling

For every Jira story:

1. Understand the acceptance criteria.
2. Identify positive scenarios.
3. Identify negative scenarios where applicable.
4. Generate meaningful test cases.
5. Generate Selenium Java implementation.
6. Use Page Object Model.
7. Add Jira story key to the test class.
8. Use meaningful method names.
9. Avoid Thread.sleep().
10. Use WebDriverWait.
11. Keep configuration reusable.

IMPORTANT:

Return ONLY valid JSON.

The JSON must have this structure:

{
    "files": [
        {
            "path": "pom.xml",
            "content": "..."
        },
        {
            "path": "src/test/java/com/automation/base/BaseTest.java",
            "content": "..."
        }
    ]
}

Every file must contain complete source code.

Do not use markdown code fences.
Do not add explanations outside the JSON.
"""


def clean_json_response(text):

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?",
            "",
            text
        )

        text = re.sub(
            r"```$",
            "",
            text
        )

    return text.strip()


def generate_selenium_project(stories):

    stories_json = json.dumps(
        stories,
        indent=2,
        ensure_ascii=False
    )

    prompt = f"""
Generate a complete Selenium Java automation project
for the following Jira user stories.

JIRA STORIES:

{stories_json}

The generated project must include:

1. pom.xml
2. BaseTest.java
3. DriverFactory.java
4. Page Objects
5. TestNG test classes
6. testng.xml
7. config.properties
8. README.md

Use this package:

com.automation

Use:

src/test/java/com/automation/

for Java source files.

Use:

src/test/resources/

for configuration and TestNG files.

Every test class must reference its Jira story key.

Example:

/*
 * Jira Story: AVD-6
 */

Create realistic Selenium test automation based
on the information available in the Jira story.

If URLs or selectors are not provided by Jira,
use clearly marked configurable placeholders
rather than inventing real application selectors.

Return only the required JSON.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            SYSTEM_PROMPT,
            prompt
        ]
    )

    raw_text = response.text

    cleaned = clean_json_response(raw_text)

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise Exception(
            f"Gemini returned invalid JSON: {exc}\n\n"
            f"Response:\n{raw_text}"
        )

    if "files" not in result:
        raise Exception(
            "Gemini response does not contain 'files'"
        )

    return result["files"]
import os
import json
import re
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

PRIMARY_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

FALLBACK_MODELS = [
    PRIMARY_MODEL,
    "gemini-3.6-flash",
    "gemini-3.5-flash"
]

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing")

client = genai.Client(
    api_key=GEMINI_API_KEY
)


SYSTEM_PROMPT = """
You are a Senior QA Automation Engineer and Java Selenium
Automation Architect.

Your job is to convert Jira user stories into a complete
Selenium Java TestNG automation project.

Technology requirements:

- Java 17
- Selenium WebDriver
- TestNG
- Maven
- Page Object Model
- WebDriverManager
- WebDriverWait
- Assertions
- Reusable configuration
- Clean Java syntax
- Proper package structure
- No Thread.sleep()

For every Jira story:

1. Understand the story.
2. Identify positive test scenarios.
3. Identify negative test scenarios where applicable.
4. Generate Selenium automation.
5. Use Page Object Model.
6. Add the Jira story key to the test class.
7. Use meaningful test method names.
8. Use explicit waits.
9. Use TestNG assertions.
10. Keep configuration reusable.

IMPORTANT:

Return ONLY valid JSON.

The JSON must have exactly this structure:

{
    "files": [
        {
            "path": "pom.xml",
            "content": "complete file content"
        }
    ]
}

Every file must contain complete source code.

Do not use markdown code fences.

Do not add explanations outside the JSON.

IMPORTANT JAVA QUALITY RULES:

Before returning the response, verify that:

- Java imports contain proper spaces.
- Method declarations contain proper spaces.
- Every opening brace has a matching closing brace.
- Every Java statement ends with a semicolon where required.
- Package declarations are correct.
- Class names match file names.
- Maven XML is valid.
- TestNG XML is valid.
- No accidental text is inserted into Java code.
- No Thread.sleep() is used.

If Jira does not provide actual URLs or selectors,
use clearly marked placeholders.

Do NOT invent real application selectors.
"""


def clean_json_response(text):

    text = text.strip()

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"```$",
            "",
            text
        )

    return text.strip()


def call_gemini(model, prompt):

    print(f"Trying Gemini model: {model}")

    response = client.models.generate_content(
        model=model,
        contents=[
            SYSTEM_PROMPT,
            prompt
        ]
    )

    return response.text


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

The project MUST include:

1. pom.xml

2. src/test/java/com/automation/base/BaseTest.java

3. src/test/java/com/automation/factory/DriverFactory.java

4. src/test/java/com/automation/utils/ConfigReader.java

5. src/test/java/com/automation/pages/BasePage.java

6. Page Object classes required by the stories.

7. TestNG test classes.

8. src/test/resources/config.properties

9. src/test/resources/testng.xml

10. README.md

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
 * Jira Story: SCRUM-6
 */

Generate realistic Selenium test automation based
ONLY on information available in the Jira story.

If the Jira story does not contain application URLs,
HTML selectors, usernames, passwords, or exact UI details,
use configurable placeholders.

Do not pretend that unknown selectors are real.

Before returning the JSON, carefully validate every
Java file for syntax mistakes.

Return ONLY JSON.
"""

    last_error = None

    for model in FALLBACK_MODELS:

        for attempt in range(2):

            try:

                raw_text = call_gemini(
                    model,
                    prompt
                )

                cleaned = clean_json_response(
                    raw_text
                )

                result = json.loads(cleaned)

                if "files" not in result:
                    raise Exception(
                        "Gemini response does not contain 'files'"
                    )

                files = result["files"]

                if not isinstance(files, list):
                    raise Exception(
                        "'files' must be a list"
                    )

                if len(files) == 0:
                    raise Exception(
                        "Gemini returned zero files"
                    )

                # Basic validation
                for file in files:

                    if "path" not in file:
                        raise Exception(
                            "Generated file is missing path"
                        )

                    if "content" not in file:
                        raise Exception(
                            f"Generated file "
                            f"{file.get('path')} "
                            f"is missing content"
                        )

                print(
                    f"Gemini generation successful "
                    f"using {model}"
                )

                return files

            except Exception as exc:

                last_error = exc

                print(
                    f"Gemini attempt failed "
                    f"using {model}: {exc}"
                )

                if attempt == 0:

                    print(
                        "Retrying Gemini in 3 seconds..."
                    )

                    time.sleep(3)

        print(
            f"Trying next Gemini model..."
        )

    raise Exception(
        "Gemini automation generation failed "
        f"after trying all models.\n"
        f"Last error: {last_error}"
    )
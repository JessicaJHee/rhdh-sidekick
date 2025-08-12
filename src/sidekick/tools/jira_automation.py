import subprocess
import os
from dotenv import load_dotenv

from loguru import logger

from sidekick.tools.jira_toolkit import _get_jira_client
from rich.table import Table
from rich.console import Console

load_dotenv()

server_url = os.getenv("JIRA_URL")
username = os.getenv("JIRA_USERNAME")
token = os.getenv("JIRA_PERSONAL_TOKEN")

logger.debug(f"Initializing JIRA client with server_url: {server_url}")
logger.debug(f"Username provided: {'Yes' if username else 'No'}")
logger.debug(f"Token provided: {'Yes' if token else 'No'}")

JIRA_FILTER = (
    '(project = RHIDP OR project in ("Red Hat Developer Hub Bugs", rhdhsupp)) AND status != closed AND (Team is EMPTY OR component is EMPTY) AND issuetype not in (Sub-task, Epic, Feature, "Feature Request", Outcome) ORDER BY created DESC, priority DESC'
)
SIDEKICK_CLI = ["uv", "run", "sidekick", "jira-triager", "triage"]

def main():
    if not server_url:
        raise ValueError("JIRA_URL environment variable is required")
    if not token:
        raise ValueError("JIRA_PERSONAL_TOKEN environment variable is required")

    logger.debug(f"Connecting to Jira at {server_url}")

    jira = _get_jira_client()
    issues = jira.search_issues(JIRA_FILTER, maxResults=100)
    table = Table(title="Jira Triager Results")
    table.add_column("Issue Key", style="cyan", no_wrap=True)
    table.add_column("Team Assignment", style="magenta")
    table.add_column("Component Assignment", style="green")
    console = Console()
    for issue in issues:
        print(f"Triaging {issue.key} ...")
        # Call your CLI for each issue
        result = subprocess.run(SIDEKICK_CLI + [issue.key], capture_output=True, text=True)
        team = component = ""
        if result.returncode == 0:
            # Try to parse the output as JSON
            import json
            try:
                output = result.stdout.strip()
                # Find the first JSON object in the output
                import re
                match = re.search(r'\{.*\}', output, re.DOTALL)
                if match:
                    data = json.loads(match.group(0))
                    team = data.get("team", "")
                    component = data.get("component", "")
            except Exception:
                team = component = "parse error"
        else:
            team = component = "error"

        table.add_row(issue.key, team or "", component or "")

    console.print(table)


if __name__ == "__main__":
    main() 
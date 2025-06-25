from flask import Flask, render_template_string
from datetime import datetime

import os
import re

from list_active_pull_requests import fetch_active_pull_requests

app = Flask(__name__)

template = """
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <title>Pull Requests</title>
  <style>
    body { font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 2em; }
    .card { background: #fff; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 1em; margin-bottom: 1em; }
    .repo { font-weight: bold; color: 343a40; }
    .repo-link { text-decoration: none; color: #007bff; }
    .title { margin-top: 0.5em; }
    .branches { color: #343a40; font-size: 0.9em; margin-top: 0.25em; }
    .date { color: #343a40; font-size: 0.9em; margin-top: 0.25em; }
    .reviewers { margin-top: 0.5em; }
    .reviewers img { width: 24px; height: 24px; border-radius: 50%; margin-right: 0.25em; }
  </style>
</head>
<body>
  <h1>Pull Requests Ativos</h1>
  {% for pr in pull_requests %}
    <div class="card">
      <div class="repo">
        <a class="repo-link" href="{{ pr.prUrl }}" target="_blank">
          {{ pr.repository.name }} #{{ pr.pullRequestId }}
        </a>
        <a class="repo-link" href="{{ pr.userStoryUrl }}" target="_blank">
          {% if pr.userStoryNumber %}
            User Story {{ pr.userStoryNumber }}
          {% endif %}
        </a>
      </div>
      <div class="title">{{ pr.title }}</div>
      <div class="branches">{{ pr.sourceBranchName }} → {{ pr.targetBranchName }}</div>
      <div class="date">Criada em {{ pr.creationDateFormatted }} por {{ pr.creatorName }}</div>
      <div class="reviewers">
        {% for rv in pr.reviewers %}
        <img src="{{ rv.imageUrl }}" alt="{{ rv.displayName }}" title="{{ rv.displayName }}" />
        {% endfor %}
      </div>
      </div>
    {% endfor %}
  </body>
</html>
"""


def extract_user_story_number(title: str) -> str:
    """
    Extrai o número da user story do título, considerando padrões como:
    "US #22021 - ..." ou "US23975-..."
    """
    if not title:
        return ""
    # Tenta encontrar padrões "US #12345" ou "US12345"
    match = re.search(r"US\s*#?(\d{3,})", title, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def format_date(date_str: str) -> str:
    """Return date formatted as dd/MM/yyyy HH:mm:ss."""
    # Substitui Z por +00:00
    date_str = date_str.replace("Z", "+00:00")
    # Ajusta a precisão dos microssegundos (para 6 dígitos)
    match = re.match(r"(.*\.\d{6})\d*(\+00:00)$", date_str)
    if match:
        date_str = match.group(1) + match.group(2)
    try:
        dt = datetime.fromisoformat(date_str)
    except ValueError:
        return date_str
    return dt.strftime("%d/%m %H:%M")


def strip_ref(ref_name: str) -> str:
    """Return branch name without refs/heads/ prefix."""
    prefix = "refs/heads/"
    if ref_name and ref_name.startswith(prefix):
        return ref_name[len(prefix):]
    return ref_name or ""


def get_config():
    organization = "teltelecom"
    project = "Work"
    pat = ""
    if not all([organization, project, pat]):
        raise SystemExit(
            "Please set AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, and AZURE_DEVOPS_PAT"
        )
    return organization, project, pat


@app.route("/")
def index():
    org, project, pat = get_config()
    prs = fetch_active_pull_requests(org, project, pat)
    for pr in prs:
        date_str = pr.get("creationDate")
        if date_str:
            pr["creationDateFormatted"] = format_date(date_str)
        else:
            pr["creationDateFormatted"] = ""
        pr["sourceBranchName"] = strip_ref(pr.get("sourceRefName", ""))
        pr["targetBranchName"] = strip_ref(pr.get("targetRefName", ""))
        pr["creatorName"] = pr.get("createdBy", {}).get("displayName", "")
        pr["userStoryNumber"] = extract_user_story_number(pr.get("title", ""))

        if pr["userStoryNumber"]:
            # Se quiser parametrizar, pode puxar esses valores de variáveis/env
            pr["userStoryUrl"] = (
                f"https://dev.azure.com/teltelecom/Work/_boards/board/t/Java%20Team/Stories?workitem={pr['userStoryNumber']}"
            )
        else:
            pr["userStoryUrl"] = ""

        repo = pr.get("repository", {})
        project_name = repo.get("project", {}).get("name", project)
        repo_name = repo.get("name", "")
        pr["prUrl"] = (
            f"https://dev.azure.com/{org}/{project_name}/_git/{repo_name}/pullrequest/{pr['pullRequestId']}"
        )
        pr["reviewers"] = pr.get("reviewers", [])        
    return render_template_string(template, pull_requests=prs)


if __name__ == "__main__":
    app.run(debug=True)

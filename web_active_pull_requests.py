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
  <title>Pull Requests Ativos</title>
  <style>
    body { font-family: Arial, sans-serif; background-color: #f7f7f7; padding: 2em; }
    .card { background: #fff; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 1em; margin-bottom: 1em; }
    .repo { font-weight: bold; color: #333; }
    .title { margin-top: 0.5em; }
    .date { color: #666; font-size: 0.9em; margin-top: 0.25em; }
  </style>
</head>
<body>
  <h1>Pull Requests Ativos</h1>
  {% for pr in pull_requests %}
    <div class="card">
      <div class="repo">{{ pr.repository.name }} #{{ pr.pullRequestId }}</div>
      <div class="title">{{ pr.title }}</div>
      <div class="date">Criada em {{ pr.creationDateFormatted }}</div>
    </div>
  {% endfor %}
</body>
</html>
"""


def get_config():
    organization = "teltelecom"
    project = "Work"
    pat = "8QD5bMJ1X3y81te0l2siB62HYc0VjYV2089pILjpfUAGL3VooxueJQQJ99BFACAAAAAi9eYWAAASAZDO"
    if not all([organization, project, pat]):
        raise SystemExit(
            "Please set AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, and AZURE_DEVOPS_PAT"
        )
    return organization, project, pat


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
    return dt.strftime("%d/%m/%Y %H:%M:%S")


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
    return render_template_string(template, pull_requests=prs)


if __name__ == "__main__":
    app.run(debug=True)

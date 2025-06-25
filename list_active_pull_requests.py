import os
import requests


def fetch_active_pull_requests(org: str, project: str, token: str):
    """Return active pull requests for the given project."""
    url = f"https://dev.azure.com/{org}/{project}/_apis/git/pullrequests"
    params = {
        "searchCriteria.status": "active",
        "api-version": "7.0",
    }
    response = requests.get(url, params=params, auth=("", token))
    response.raise_for_status()
    return response.json().get("value", [])


if __name__ == "__main__":
    organization = "teltelecom"
    project = "Work"
    pat = "2WcYh6n3VHm8jmqiM7PdWxUy93wBa7cNazSzqjkpQUJsmglze5KSJQQJ99BFACAAAAAi9eYWAAASAZ"
    if not all([organization, project, pat]):
        raise SystemExit(
            "Please set AZURE_DEVOPS_ORG, AZURE_DEVOPS_PROJECT, and AZURE_DEVOPS_PAT"
        )

    pull_requests = fetch_active_pull_requests(organization, project, pat)
    for pr in pull_requests:
        repo_name = pr.get("repository", {}).get("name", "")
        print(f"[{repo_name}] #{pr['pullRequestId']}: {pr['title']}")

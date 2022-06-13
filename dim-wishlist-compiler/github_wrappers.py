from os import getenv
from github import Github
from github.Repository import Repository

github_user_name = getenv("GH_UN")
assert github_user_name

github_token = getenv("GH_TOKEN")
assert github_token

g = Github(github_user_name, github_token)


def get_repo(owner: str, name: str) -> Repository:
    return g.get_repo("/".join((owner, name)))

from io import FileIO
from os import getenv
from pathlib import Path

from github import Github
from github.ContentFile import ContentFile

output_folder_path = Path.cwd()
output_path = output_folder_path / "PandaPaxxy_no_mkb_output.txt"

github_user_name = getenv("GH_UN")
assert github_user_name

github_token = getenv("GH_TOKEN")
assert github_token

g = Github(github_user_name, github_token)
repo = g.get_repo("48klocs/dim-wish-list-sources")
content_files: list[ContentFile] = repo.get_contents("PandaPaxxy")

with FileIO(output_path, mode="wb+") as output_file:
    for content in content_files:
        if not content.content or content.content == "":
            print(f"Skipping {content.name}... no content.")
            continue

        if "mkb" in content.name:
            print(f"Skipping {content.name}... for mouse and keyboard.")
            continue

        print(f"Downloading {content.name}...")
        output_file.write(content.decoded_content)
        print(f"{content.name} written to {str(output_path)}.")

print()
print(f"{str(output_path)} ready for DIM.")

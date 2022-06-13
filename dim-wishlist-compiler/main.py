import requests
from io import BytesIO, FileIO
from os import getenv
from pathlib import Path
from typing import Iterable, Union

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


def bytes_to_str(x: bytes) -> str:
    return x.decode("utf-8")


def clean_line(line: Union[str, bytes], debug: bool = False) -> str:
    if isinstance(line, bytes):
        line = bytes_to_str(line)

    cleaned = line.strip().replace('"', "").replace("\\n", "").rstrip("'")

    if debug:
        print(f"original line = {line} ::: cleaned line = {cleaned}")

    return cleaned


def clean_leading_line(line: Union[str, bytes], debug: bool = False) -> str:
    if isinstance(line, bytes):
        line = bytes_to_str(line)

    split_line = line.split(":")
    leading_line_contents = ":".join(split_line[1:])
    cleaned = clean_line(leading_line_contents)

    if debug:
        print(f"original line = {line} ::: cleaned line = {cleaned}")

    return cleaned


title_lines: list[str] = []
description_lines: list[str] = []
roll_lines: list[str] = []
unique_rolls: set[str] = set()


def parse_contents(lines: Iterable[bytes]) -> int:
    roll_count = 0
    for index, line in enumerate(lines):
        if index == 0:
            title_lines.append(clean_leading_line(line, True))
        elif index == 1:
            description_lines.append(clean_leading_line(line, True))
        else:
            add_line = True
            roll_line = clean_line(line)
            if roll_line.startswith("dimwishlist:"):
                if roll_line in unique_rolls:
                    add_line = False
                else:
                    roll_count += 1
                    unique_rolls.add(roll_line)

            if add_line:
                roll_lines.append(roll_line)

    print(f"Found {roll_count} rolls.")


contents: list[ContentFile] = sorted(content_files, key=lambda f: f.last_modified)
for content in contents:
    if "mkb" in content.name:
        print(f"Skipping {content.name}... for mouse and keyboard.")
        continue

    if content.content:
        print(f"Parsing {content.name}...")
        with BytesIO(content.decoded_content) as content_bytes:
            parse_contents(content_bytes.readlines())
    else:
        download_url = content.raw_data["download_url"]
        print(f"Downloading remote contents from {download_url}...")
        with requests.get(download_url, stream=True) as remote_contents:
            parse_contents(remote_contents.iter_lines())


def write_line(file: FileIO, line: str) -> None:
    file.write(f"{line}\n".encode("utf-8"))


with FileIO(output_path, mode="wb+") as output_file:
    write_line(output_file, f"title:{'|'.join(title_lines)}")
    write_line(output_file, f"description:{'|'.join(description_lines)}")
    for line in roll_lines:
        write_line(output_file, line)

print()
print(f"{str(output_path)} ready for DIM.")

total_roll_count = len(list(unique_rolls))
print(f"Wish list contains {total_roll_count} rolls.")

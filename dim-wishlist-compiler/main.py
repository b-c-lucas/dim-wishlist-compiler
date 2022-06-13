import requests
from collections import defaultdict
from datetime import datetime
from io import BytesIO, FileIO
from pathlib import Path
from typing import Iterable, Union

from github.Commit import Commit
from github.ContentFile import ContentFile
from github_wrappers import get_repo
from helpers import bytes_to_str

OUTPUT_FOLDER_PATH = Path.cwd()
OUTPUT_PATH = OUTPUT_FOLDER_PATH / "PandaPaxxy_no_mkb_output.txt"


TITLE_LINES: list[str] = []
DESCRIPTION_LINES: list[str] = []
ROLL_LINES: list[str] = []
UNIQUE_ROLLS: set[str] = set()


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


def parse_contents(lines: Iterable[bytes]) -> int:
    roll_count = len(list(UNIQUE_ROLLS))

    for index, line in enumerate(lines):
        if index == 0:
            TITLE_LINES.append(clean_leading_line(line))
        elif index == 1:
            DESCRIPTION_LINES.append(clean_leading_line(line))
        else:
            add_line = True
            roll_line = clean_line(line)
            if roll_line.startswith("dimwishlist:"):
                if roll_line in UNIQUE_ROLLS:
                    add_line = False
                else:
                    UNIQUE_ROLLS.add(roll_line)

            if add_line:
                ROLL_LINES.append(roll_line)

    print(f"Found {len(list(UNIQUE_ROLLS)) - roll_count} rolls.")


def write_line(file: FileIO, line: str) -> None:
    file.write(f"{line}\n".encode("utf-8"))


repo = get_repo("48klocs", "dim-wish-list-sources")
repo_contents: list[ContentFile] = repo.get_contents("PandaPaxxy")

filtered_contents: dict[str, ContentFile] = {
    c.path: c for c in repo_contents if "mkb" not in c.name
}

unhandled_file_names: set[str] = set(filtered_contents.keys())

commit_date_files: dict[datetime, set[str]] = defaultdict(set)

print("Ordering files by original commit date...")

commits: list[Commit] = repo.get_commits()
for commit in sorted(commits, key=lambda c: c.commit.author.date):
    for file in commit.files:
        if file.filename not in unhandled_file_names:
            continue

        print(f"Found commit '{commit.commit.sha}' for file '{file.filename}'.")

        unhandled_file_names.remove(file.filename)
        commit_date_files[commit.commit.author.date].add(file.filename)

    if len(list(unhandled_file_names)) == 0:
        break


if len(list(unhandled_file_names)) > 0:
    raise Exception(
        f"All files not found in commit history: {list(unhandled_file_names)}"
    )

print("Commits found for all files.")
print()

ordered_contents: list[ContentFile] = []
for commit_date in sorted(commit_date_files.keys()):
    for file_name in sorted(commit_date_files[commit_date]):
        ordered_contents.append(filtered_contents[file_name])

for content in ordered_contents:
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


with FileIO(OUTPUT_PATH, mode="wb+") as output_file:
    write_line(output_file, f"title:{'|'.join(TITLE_LINES)}")
    write_line(output_file, f"description:{'|'.join(DESCRIPTION_LINES)}")
    for line in ROLL_LINES:
        write_line(output_file, line)

print()
print(f"{str(OUTPUT_PATH)} ready for DIM.")
print(f"Wish list contains {len(list(UNIQUE_ROLLS))} rolls.")

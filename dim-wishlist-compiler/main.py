import requests
from io import BytesIO, FileIO
from pathlib import Path
from typing import Iterable, Union

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
contents: list[ContentFile] = sorted(
    repo.get_contents("PandaPaxxy"), key=lambda f: f.last_modified
)
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


with FileIO(OUTPUT_PATH, mode="wb+") as output_file:
    write_line(output_file, f"title:{'|'.join(TITLE_LINES)}")
    write_line(output_file, f"description:{'|'.join(DESCRIPTION_LINES)}")
    for line in ROLL_LINES:
        write_line(output_file, line)

print()
print(f"{str(OUTPUT_PATH)} ready for DIM.")
print(f"Wish list contains {len(list(UNIQUE_ROLLS))} rolls.")

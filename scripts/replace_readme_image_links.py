"""Replace relative links with absolute links in README.md, so images also work on PyPI.
"""
import re

if __name__ == "__main__":
    FILE_PATH = "README.md"
    GITHUB_PATH = "sradc/lr_schedules/master"

    with open(FILE_PATH, "r") as file:
        data = file.read()

    # Regular expression to find the markdown image syntax
    pattern = r"\!\[.*\]\((README_files/.*\.png)\)"
    replacement = r"![\1](https://raw.githubusercontent.com/" + GITHUB_PATH + r"/\1)"

    # Substitute the pattern with the replacement
    new_data = re.sub(pattern, replacement, data)

    with open(FILE_PATH, "w") as file:
        file.write(new_data)

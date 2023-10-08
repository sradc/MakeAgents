"""Replace relative links with absolute links in README.md, so images also work on PyPI.
"""
import re

if __name__ == "__main__":
    FILE_PATH = "README.md"
    GITHUB_PATH = "sradc/MakeAgents/main"

    with open(FILE_PATH, "r") as file:
        data = file.read()

    # Find links referencing README_files/ and replace them with absolute links
    pattern = r"(README_files/.*\.(png|jpg))"
    replacement = r"https://raw.githubusercontent.com/" + GITHUB_PATH + r"/\1"

    # Substitute the pattern with the replacement
    new_data = re.sub(pattern, replacement, data)

    with open(FILE_PATH, "w") as file:
        file.write(new_data)

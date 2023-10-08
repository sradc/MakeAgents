"""Replace relative links with absolute links in README.md, so images also work on PyPI.
"""
import re

if __name__ == "__main__":
    FILE_PATH = "README.md"
    GITHUB_PATH = "sradc/MakeAgents/main"

    with open(FILE_PATH, "r") as file:
        text = file.read()

    # Find links referencing README_files/ and replace them with absolute links
    pattern = r"(README_files/.*\.(png|jpg))"
    replacement = r"https://raw.githubusercontent.com/" + GITHUB_PATH + r"/\1"
    text = re.sub(pattern, replacement, text)

    pattern = r"(static/.*\.(png|jpg))"
    replacement = r"https://raw.githubusercontent.com/" + GITHUB_PATH + r"/\1"
    text = re.sub(pattern, replacement, text)

    with open(FILE_PATH, "w") as file:
        file.write(text)

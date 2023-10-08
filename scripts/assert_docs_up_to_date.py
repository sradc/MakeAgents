from pathlib import Path

import make_agents

if __name__ == "__main__":
    main_page_path = Path("docs/index.html")
    if main_page_path.read_text().find(make_agents.__version__) == -1:
        raise RuntimeError(
            f"Version mismatch between docs and package: {main_page_path} does not contain {make_agents.__version__}"
        )

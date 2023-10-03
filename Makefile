format:
	poetry run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place .  \
	&& poetry run black --line-length 90 .  \
	&& poetry run isort --profile black .

test:
	poetry run python -m pytest --cov=make_agents tests

# Runs the nb, to generate output / figures
execute_readme:
	poetry run python -m nbconvert --to notebook --execute README.ipynb --output README.tmp.ipynb

readme: execute_readme
	poetry run python -m nbconvert --to markdown --output README.md README.tmp.ipynb  \
	&& poetry run python scripts/replace_readme_image_links.py

# run semantic release, publish to github + pypi
release:
	if poetry run semantic-release --strict version; then \
		poetry run semantic-release changelog && \
		poetry run semantic-release publish && \
		poetry publish && \
		git push && \
		git push --tags; \
	else \
		echo "No release needs to be made."; \
	fi

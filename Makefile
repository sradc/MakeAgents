.PHONY: docs

format:
	poetry run autoflake --remove-all-unused-imports --recursive --remove-unused-variables --in-place .  \
	&& poetry run black --line-length 90 .  \
	&& poetry run isort --profile black .

test:
	poetry run python -m pytest --cov=make_agents tests

# Runs the nb, to generate output / figures
execute_readme:
	poetry run python -m nbconvert --to notebook --execute README.ipynb --output README.tmp.ipynb
# Note turned off execute_readme dependency for now, when running `readme`,
# because the `input(..)` stuff prevents it from working
# remember to use the tempfile when restore, e.g:
# readme
# poetry run python -m nbconvert --to markdown --output README.md README.tmp.ipynb  \

readme:
	poetry run python -m nbconvert --to markdown --output README.md README.ipynb  \
	&& poetry run python scripts/replace_readme_image_links.py

docs:
	poetry install && \
	if poetry run python scripts/assert_docs_up_to_date.py; then \
		echo "Docs are up to date"; \
	else \
		cd docs_creator  \
		&& $(MAKE) html  \
		&& find ../docs ! -name 'CNAME' -type f -exec rm -f {} +  \
		&& cp -r build/html/* ../docs  \
		&& touch ../docs/.nojekyll; \
	fi

serve_docs: docs
	cd docs && python -m http.server

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

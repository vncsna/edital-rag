shell:
	@poetry --directory ./app shell 

lint:
	@poetry --directory ./app run ruff format --config app/pyproject.toml .
	@poetry --directory ./app run ruff check --config app/pyproject.toml --fix .

install:
	@poetry --directory ./app install

run:
	@poetry --directory ./app run streamlit run app/app/main.py

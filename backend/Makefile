PACKAGE_PATH = ./src
APP = app/main.py
TEST_DIR = app/tests/
PYTHON3_BIN = $(shell which python3)


.PHONY: help
help: ## Display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development 
.PHONY: install
install: ## Install dependencies
	poetry install

.PHONY: run
run: ## Run the application
	docker compose down
	docker compose up -d --build

.PHONY: stop
stop: ## Stop the application
	docker compose down

.PHONY: run-dev
run-dev: ## Run the aplication in dev mode
	poetry run fastapi dev $(APP)
  
.PHONY: db-up
db-up: ## Create database container
	docker compose up -d

.PHONY: db-down
db-down: ## Destroy database container
	docker compose down

.PHONY: build
build: ## Build the container application image
	docker build -t rachadez-backend .

.PHONY: test
test: ## Run unit tests
	poetry run pytest -v

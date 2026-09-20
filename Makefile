# --- Configuration ---
PROJECTNAME := metronomic
PYTHON ?= 3.12
UV_VENV ?= .venv
UV_INSTALLED := .uv-installed
DEPS_INSTALLED := ${UV_VENV}/.deps-installed
TESTDIR := tests/
COVERAGE ?= true

# --- Color Setup ---
GREEN := \033[0;32m
CYAN := \033[0;36m
YELLOW := \033[1;33m
RESET := \033[0m

# --- Help Command ---
.PHONY: help
help:
	@echo "\n${YELLOW}metronomic Development Commands${RESET}\n"
	@echo "  ${CYAN}install${RESET}      - Install package with test dependencies"
	@echo "  ${CYAN}test${RESET}         - Run Python tests (COVERAGE=false to skip coverage)"
	@echo "  ${CYAN}test-rust${RESET}    - Run Rust tests"
	@echo "  ${CYAN}conformance${RESET}  - Run golden suite against BOTH implementations"
	@echo "  ${CYAN}build${RESET}        - Build Python distributions and release binary"
	@echo "  ${CYAN}clean${RESET}        - Remove build artifacts and caches"
	@echo ""
	@echo "${YELLOW}Variables:${RESET}\n"
	@echo "  PYTHON=${PYTHON}		- Python version for the uv environment"
	@echo "  UV_VENV=${UV_VENV}		- Path to virtual environment"
	@echo "  COVERAGE=${COVERAGE}		- Enable coverage (true/false)"
	@echo ""

# --- uv Installation ---
${UV_INSTALLED}:
	@command -v uv >/dev/null 2>&1 || { \
		echo "${GREEN}Installing uv...${RESET}"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@touch ${UV_INSTALLED}

# --- Installation ---
${DEPS_INSTALLED}: pyproject.toml | ${UV_INSTALLED}
	@echo "${GREEN}Syncing dependencies into ${UV_VENV}...${RESET}"
	@UV_PROJECT_ENVIRONMENT=${UV_VENV} uv sync --python ${PYTHON} --extra test
	@touch ${DEPS_INSTALLED}

.PHONY: install
install: ${DEPS_INSTALLED}
	@echo "${CYAN}Environment ready at ${UV_VENV}${RESET}"

# --- Testing ---
.PHONY: test
test: ${DEPS_INSTALLED}
	@echo "${GREEN}Running Python tests...${RESET}"
ifeq ($(COVERAGE),true)
	@UV_PROJECT_ENVIRONMENT=${UV_VENV} uv run --python ${PYTHON} coverage run -m pytest ${TESTDIR} -q
	@UV_PROJECT_ENVIRONMENT=${UV_VENV} uv run --python ${PYTHON} coverage report -m
	@UV_PROJECT_ENVIRONMENT=${UV_VENV} uv run --python ${PYTHON} coverage xml
else
	@UV_PROJECT_ENVIRONMENT=${UV_VENV} uv run --python ${PYTHON} -m pytest ${TESTDIR} -q
endif

.PHONY: test-rust
test-rust:
	@echo "${GREEN}Running Rust tests...${RESET}"
	@cargo test --manifest-path rust/Cargo.toml -q

# --- Conformance ---
.PHONY: conformance
conformance: ${DEPS_INSTALLED}
	@echo "${GREEN}Conformance: Python implementation...${RESET}"
	@tests/run_conformance.sh ${UV_VENV}/bin/metronomic
	@echo "${GREEN}Conformance: Rust implementation...${RESET}"
	@cargo build --manifest-path rust/Cargo.toml -q
	@tests/run_conformance.sh rust/target/debug/metronomic

# --- Building ---
.PHONY: build
build: ${UV_INSTALLED}
	@echo "${GREEN}Building Python distributions...${RESET}"
	@uv build
	@echo "${GREEN}Building release binary...${RESET}"
	@cargo build --manifest-path rust/Cargo.toml --release -q
	@echo "${CYAN}Artifacts at dist/ and rust/target/release/${PROJECTNAME}${RESET}"

# --- Cleaning ---
.PHONY: clean
clean:
	@echo "${GREEN}Cleaning build artifacts...${RESET}"
	@rm -rf dist/ build/ *.egg-info/ src/*.egg-info/
	@rm -rf ${UV_VENV} ${UV_INSTALLED}
	@rm -rf .pytest_cache/ rust/target/
	@rm -f coverage.xml .coverage
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "${CYAN}Clean complete.${RESET}"

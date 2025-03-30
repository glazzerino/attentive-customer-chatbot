# CLAUDE.md - Agent Guidelines

## Project Overview
WhatsApp E-Commerce Bot using FastAPI, SQLite, Redis, and Anthropic Claude API.

## Build/Run Commands
- **Start Server**: `uvicorn main:app --reload`
- **Run Tests**: `pytest tests/`
- **Run Single Test**: `pytest tests/test_file.py::test_function -v`
- **Lint Code**: `flake8 .`
- **Type Check**: `mypy .`

## Code Style Guidelines
- **Imports**: Stdlib first, then third-party, then local modules; alphabetically sorted within groups
- **Formatting**: 4 spaces indentation, 88 character line limit
- **Types**: Type annotations required for all function parameters and return values
- **Naming**: 
  - snake_case for variables/functions
  - PascalCase for classes
  - UPPER_CASE for constants
- **Error Handling**: Use try/except blocks with specific exceptions
- **Abstractions**: Maintain clean interfaces for messaging platforms and LLM providers
- **Documentation**: Docstrings for all public functions and classes
- **Testing**: Write unit tests for all new functionality

## Architecture
Follow component abstractions from spec.md when implementing new features.
# Contributing to psx-data

Thank you for your interest in contributing to psx-data.

psx-data is an open-source project, and contributions are welcome. This document explains the development workflow and expectations for contributing to the project.

## Before You Start

Please:

1. Read the project documentation.
2. Check existing issues and pull requests before starting significant work.
3. Open an issue first for large features or architectural changes.
4. Keep changes focused and related to the purpose of the pull request.

## Branching Strategy

Changes should not be made directly on `main`.

Create a branch for your work:

```bash
git switch main
git pull origin main
git switch -c <branch-name>

```

### Branch Prefixes

Recommended prefixes:

- feature/ — new functionality
- fix/ — bug fixes
- docs/ — documentation changes
- test/ — test changes
- refactor/ — code restructuring
- chore/ — maintenance and project configuration

### Examples

feature/announcements-client
fix/announcement-parser
docs/update-installation-guide
test/announcements-client
refactor/http-client
chore/update-ci


## Development Environment

### Requirements

- Python 3.11+
- Git

Create a virtual environment:

```bash
python -m venv .venv

```

## Making Changes

Keep changes small and focused.

### Before submitting a pull request:

- Run the test suite.
- Make sure the project installs successfully.
- Review your changes with Git.
- Make sure no unnecessary files or dependencies are included.

### Run Tests
```bash
python -m unittest discover -s tests -v
```

### Check Git Status
```bash
git status
```

### Review Changes
```bash
git diff
```

## Dependencies

psx-data aims to minimize third-party dependencies.
Before adding a dependency, consider whether the functionality can reasonably be implemented using the Python standard library.

### Do not add a third-party dependency solely for convenience without considering:

- Whether the standard library can provide the functionality
- Maintenance status of the dependency
- Security implications
- Project size and complexity
- Long-term maintenance cost

New dependencies should be explained in the pull request.

### Commit Messages

Use clear and descriptive commit messages.

The project generally follows this format:
```bash
type: short description
```

### Recommended types include:

- feat: — new functionality
- fix: — bug fix
- docs: — documentation
- test: — tests
- refactor: — code restructuring
- chore: — maintenance

### Examples:

- feat: add PSX announcements client
- fix: handle empty announcement responses
- docs: update development guide
- test: add announcement parser tests
- refactor: simplify HTTP client
- chore: update GitHub Actions workflow

Keep commits focused on a single logical change where practical.

### Pull Requests

All changes to main must be submitted through a pull request.

A pull request should:

- Clearly describe what changed
- Explain why the change was needed
- Include relevant tests
- Keep unrelated changes out of the PR
- Pass the required GitHub Actions checks
- Be reviewed before merging

The pull request description should provide enough information for reviewers and maintainers to understand the change.

### Code Review

Pull requests are subject to code review.

Reviewers may request:

- Code changes
- Additional tests
- Documentation updates
- Clarification of implementation details
- Changes to the implementation approach

Contributors should address review feedback before merging.

### Continuous Integration

GitHub Actions automatically runs the project's test suite for pull requests targeting main.

Required checks must pass before a pull request can be merged.

Do not bypass failing tests. Investigate and fix the underlying problem.

### Merging

The main branch is protected.

Changes should be merged only after:

- Required checks pass.
- Required review is completed.
- Requested changes have been addressed.

Contributors should not force-push to protected branches.

### Documentation

Documentation is part of the project.

When a change affects how users install, configure, develop, or use psx-data, update the relevant documentation as part of the same change.

### Reporting Bugs

When reporting a bug, provide as much relevant information as possible, including:

- What you expected to happen
- What actually happened
- Steps to reproduce the problem
- Python version
- Operating system
- Relevant error messages or logs

A minimal reproducible example is helpful when possible.

### Feature Requests

Feature requests are welcome.

For larger features, open an issue before implementing the feature so that the proposed approach can be discussed before significant development work begins.

## License

By contributing to psx-data, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
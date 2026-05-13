# Contributing to AGenNext Protocols

## Development Setup

```bash
git clone https://github.com/AGenNext/AGenNext-Protocols.git
cd AGenNext-Protocols
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Quality Checks

```bash
ruff check .
black --check .
pytest
```

## Pull Requests

- Create a focused branch
- Add tests when applicable
- Ensure CI passes
- Update documentation when behavior changes

## Security Issues

Please report vulnerabilities privately as described in `SECURITY.md`.

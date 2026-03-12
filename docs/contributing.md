# Contributing Guide — OVOS GUI

Guidelines for contributing to the `ovos-gui` project.

## Welcome!

We appreciate contributions to the OVOS GUI system. Whether you're fixing bugs, adding features, improving documentation, or building adapters — thank you for helping!

---

## Before You Start

1. **Read the [Architecture](architecture.md)** to understand the system design
2. **Check [existing issues](https://github.com/OpenVoiceOS/ovos-gui/issues)** — your idea might already be in progress
3. **Fork the repository** and create a feature branch from `dev`
4. **Set up your environment** (see Setup section below)

---

## Setup

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/OpenVoiceOS/ovos-gui.git
cd ovos-gui

# Install in development mode
uv pip install -e .

# Install test dependencies
uv pip install pytest pytest-cov
```

### 2. Run Tests

```bash
# Run all tests
uv run pytest test/unittests/ -v

# With coverage
uv run pytest test/unittests/ --cov=ovos_gui --cov-report=html
```

### 3. Check Code Style

```bash
# Install flake8
uv pip install flake8

# Check style
flake8 ovos_gui/
```

---

## Code Standards

### Python Version
- **Minimum**: Python 3.10
- **Support**: 3.10, 3.11, 3.12, 3.13

### Style
- **Follow**: PEP 8
- **Type hints**: Mandatory for all functions and classes
- **Docstrings**: Required (Google style)
- **Imports**: Explicit only (no relative imports)

### Example

```python
from ovos_gui.namespace import NamespaceManager

def process_page_request(
    namespace: str,
    page_name: str,
    data: dict
) -> bool:
    """Process a page show request.

    Args:
        namespace: The skill namespace identifier
        page_name: Name of the page to display
        data: Template data (must include required fields)

    Returns:
        True if successful, False if validation failed

    Raises:
        ValueError: If namespace is invalid
    """
    manager = NamespaceManager()
    return manager.show_page(namespace, page_name, data)
```

---

## Making Changes

### 1. Create a Feature Branch

```bash
# Branch naming: feature/<description> or fix/<issue-number>
git checkout -b feature/improve-namespace-caching
```

### 2. Make Your Changes

- **Keep commits atomic** — one logical change per commit
- **Write meaningful commit messages** — explain the "why", not just the "what"
- **Update tests** — add or modify tests to cover your changes
- **Update docs** — if you change public APIs, update `docs/`

### 3. Write Tests

All code changes require tests. Test coverage must remain ≥85%.

```python
# test/unittests/test_my_feature.py
import unittest
from ovos_gui.my_module import MyFeature

class TestMyFeature(unittest.TestCase):
    """Test my new feature."""

    def setUp(self):
        """Setup test fixtures."""
        self.feature = MyFeature()

    def test_basic_functionality(self):
        """Test basic behavior."""
        result = self.feature.do_something()
        self.assertIsNotNone(result)

    def test_error_handling(self):
        """Test error cases."""
        with self.assertRaises(ValueError):
            self.feature.do_something(invalid_input=True)


if __name__ == "__main__":
    unittest.main()
```

### 4. Run Tests Locally

```bash
# Run all tests
uv run pytest test/unittests/ -v

# Run specific test file
uv run pytest test/unittests/test_my_feature.py -v

# Check coverage
uv run pytest test/unittests/ --cov=ovos_gui --cov-report=term-missing
```

**Coverage must not drop below 85%.**

### 5. Check Style

```bash
flake8 ovos_gui/

# Fix common issues automatically
uv pip install black
black ovos_gui/
```

---

## Documentation

### Update Relevant Docs

If you change public APIs or behavior, update the relevant documentation:

- **New template method?** → Update `docs/templates.md`
- **New adapter feature?** → Update `docs/adapter-plugins.md`
- **Bug fix?** → Update `docs/testing-gui.md` with test example if relevant
- **Major change?** → Update `docs/architecture.md`

### Documentation Format

All documentation describing runtime behavior must cite source code:

```markdown
The `NamespaceManager.show_page()` method — `ovos_gui/namespace.py:150` —
handles page display logic and validates template data against the schema.
```

### Update MAINTENANCE_REPORT.md

After merging, the maintainers will update:
- `MAINTENANCE_REPORT.md` — Changelog entry
- `AUDIT.md` — Updated metrics
- `FAQ.md` — Any new FAQs

---

## Commit Messages

Write clear, meaningful commit messages:

```
# ✅ Good
commit: Add namespace caching for improved page load performance

Implement LRU cache for frequently accessed namespaces. Reduces
page show latency by ~10% in multi-skill scenarios.

Closes #42

# ❌ Bad
commit: fix bug
commit: update stuff
commit: WIP
```

### Format
- **First line**: Short summary (under 72 characters)
- **Blank line**
- **Body**: Explain what and why (optional)
- **Footer**: Reference issues (`Closes #123`)

---

## Pull Request Process

### 1. Push Your Branch

```bash
git push origin feature/improve-namespace-caching
```

### 2. Open a PR on GitHub

1. Go to [OpenVoiceOS/ovos-gui](https://github.com/OpenVoiceOS/ovos-gui)
2. Click "New pull request"
3. Select `dev` as the base branch
4. Provide:
   - **Title**: Concise summary
   - **Description**: What changed and why
   - **Testing**: How to verify the change
   - **Checklist**:
     - [ ] Tests pass locally
     - [ ] Coverage ≥85%
     - [ ] Code follows PEP 8
     - [ ] Docs updated
     - [ ] No breaking changes (or documented)

### 3. Address Review Feedback

- **CodeRabbit reviews** your code automatically
- **CI runs** tests and style checks
- **Address comments** by making commits (don't force-push)
- **Re-request review** when ready

### 4. Merge

Once approved:
- Rebase and squash if desired (maintainers can do this)
- Merge to `dev`
- Tag a release when appropriate

---

## Special Contribution Types

### Bug Fix

1. **Link to issue**: Reference existing issue or create one
2. **Add test**: Demonstrate the bug, then fix it
3. **Update docs**: If the bug was caused by unclear documentation

```python
def test_namespace_not_created_with_empty_skill_id(self):
    """Regression test for issue #42."""
    # Bug: empty skill_id crashed instead of raising ValueError
    with self.assertRaises(ValueError):
        self.manager.create_namespace(skill_id="")
```

### Feature

1. **Create issue first**: Discuss the feature in `#feature-requests`
2. **Design**: Get feedback before implementing
3. **Implement**: Write code, tests, and docs
4. **Demo**: Provide a clear example of usage

### Documentation

1. **No tests required** for documentation changes
2. **Verify links**: Ensure all cross-references work
3. **Check formatting**: Preview markdown rendering

### Adapter Plugin

If you're building a custom adapter:

1. **Use the template**: See [Adapter Plugin System](adapter-plugins.md)
2. **Don't modify ovos-gui core** — adapters are separate packages
3. **Test independently**: Your adapter should work with current ovos-gui
4. **Link from docs**: Add to "community adapters" list

---

## Large Changes

For major architectural changes or refactors:

1. **Open a discussion** in [GitHub Discussions](https://github.com/OpenVoiceOS/ovos-gui/discussions)
2. **Outline the proposal** with pros/cons
3. **Get consensus** from maintainers
4. **Implement iteratively** with regular feedback

---

## Code Review

### What Reviewers Check

- **Correctness**: Does the code do what it claims?
- **Tests**: Are there adequate tests? Does coverage stay ≥85%?
- **Style**: Does it follow PEP 8 and project conventions?
- **Docs**: Are APIs documented? Are changes explained?
- **Breaking changes**: Will this break existing code?

### What to Expect

- **Constructive feedback**: Reviews are helpful, not personal
- **Multiple rounds**: Expect back-and-forth on complex PRs
- **Time**: We're volunteers; reviews may take time
- **Approval**: Once approved, maintainers merge

---

## Questions?

- **GitHub Issues**: For bugs and features
- **GitHub Discussions**: For questions and design discussions
- **[Community Forum](https://openvoiceos.com/forum)**: For broader questions
- **[Discord](https://discord.gg/OpenVoiceOS)**: Real-time chat

---

## Code of Conduct

We're committed to a welcoming and inclusive community. Please:

- Be respectful and constructive
- Welcome diverse perspectives
- Report violations to the OVOS team

---

## Thank You!

Every contribution — no matter how small — helps OVOS better. Thank you for investing your time and effort!

---

## See Also

- **[Architecture](architecture.md)** — System design
- **[Testing Guide](testing-gui.md)** — How to write tests
- **[Adapter System](adapter-plugins.md)** — Building custom adapters
- **[OVOS Contributing Guide](https://github.com/OpenVoiceOS/ovos-core/blob/dev/CONTRIBUTING.md)** — Core project guidelines

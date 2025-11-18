# Release Management Guide

This guide explains how to create and manage releases for the AOP project.

## Release Process

### 1. Pre-Release Checklist

Before creating a release, ensure:

- [ ] All tests pass: `pytest tests/`
- [ ] Code coverage is adequate: `pytest --cov=aop`
- [ ] Type checking passes: `mypy aop` (or warnings documented)
- [ ] Security scan passes: `bandit -r aop/`
- [ ] CHANGELOG.md is updated with all changes
- [ ] Version number updated in `pyproject.toml`
- [ ] README.md is accurate and up-to-date
- [ ] All examples work correctly
- [ ] Documentation is current

### 2. Version Numbering

AOP follows [Semantic Versioning](https://semver.org/) (SemVer):

**Format:** `MAJOR.MINOR.PATCH[-PRERELEASE]`

**Examples:**
- `0.1.0-alpha` - Alpha release (current)
- `0.1.0-beta` - Beta release
- `0.1.0-rc.1` - Release candidate 1
- `0.1.0` - Stable release
- `0.2.0` - Minor version bump (new features)
- `1.0.0` - Major version (stable API, breaking changes allowed after this)

**Rules:**
- **Alpha (0.x.0-alpha)**: Experimental, API may change drastically
- **Beta (0.x.0-beta)**: Feature complete, API stabilizing, may have bugs
- **RC (0.x.0-rc.N)**: Release candidate, production-ready testing
- **Stable (1.0.0+)**: Production-ready, follows SemVer strictly

**When to bump:**
- **MAJOR**: Breaking API changes (after 1.0.0)
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible
- **PRERELEASE**: Alpha, beta, rc tags

### 3. Update Version Number

Edit `pyproject.toml`:

```toml
[project]
name = "aop"
version = "0.1.0-alpha"  # ← Update this
```

### 4. Update CHANGELOG.md

Move items from `[Unreleased]` to new version section:

```markdown
## [Unreleased]
<!-- Empty for now -->

## [0.1.0-alpha] - 2025-01-15

### Added
- Feature 1
- Feature 2

### Fixed
- Bug fix 1
```

**Date Format:** `YYYY-MM-DD`

**Categories:**
- **Added** - New features
- **Changed** - Changes to existing features
- **Deprecated** - Features marked for removal
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security fixes

### 5. Commit Changes

```bash
# Stage version and changelog
git add pyproject.toml CHANGELOG.md

# Commit with conventional commit message
git commit -m "chore: Release v0.1.0-alpha

- Update version to 0.1.0-alpha
- Update CHANGELOG with release notes
- Prepare for initial PyPI release
"

# Push to GitHub
git push origin main
```

### 6. Create Git Tag

```bash
# Create annotated tag
git tag -a v0.1.0-alpha -m "Release v0.1.0-alpha

First alpha release of AOP (Agentic Observability Protocol).

Key features:
- Universal event logging for AI agents
- MCP, A2A, AP2 protocol support
- SQLite and PostgreSQL storage
- Web dashboard with live updates
- CLI tools for querying and analytics
- Export to JSON, CSV, TOON, OTEL, Prometheus

See CHANGELOG.md for full details.
"

# Push tag to GitHub
git push origin v0.1.0-alpha
```

### 7. Create GitHub Release

**Option A: Via GitHub Web UI**

1. Go to: https://github.com/aop-protocol/aop/releases/new
2. **Tag version:** `v0.1.0-alpha`
3. **Release title:** `v0.1.0-alpha - Initial Alpha Release`
4. **Description:** Copy from CHANGELOG.md and add:

```markdown
# AOP v0.1.0-alpha

First alpha release of AOP (Agentic Observability Protocol).

## 🎯 What is AOP?

Universal observability protocol for AI agents. Like a flight recorder for agentic systems.

## ✨ Key Features

- 🔒 Privacy-First - Local storage, you own your data
- ⚡ Fast - <1ms P99 overhead
- 🌍 Protocol-Agnostic - MCP, A2A, AP2 support
- 📊 Powerful Analytics - Trace reconstruction, metrics
- 🎯 Simple API - 1-line decorator

## 📦 Installation

\`\`\`bash
pip install aop[cli,dashboard]
\`\`\`

## 📝 What's New

See [CHANGELOG.md](CHANGELOG.md) for complete details.

### Highlights

- Universal event logging system
- MCP server integration (FastMCP + official SDK)
- Web dashboard with live updates
- CLI tools for querying and analytics
- Export to 5 formats (JSON, CSV, TOON, OTEL, Prometheus)
- 384 passing tests, 74% coverage

## ⚠️ Alpha Notice

This is an **alpha release**. The API may change in future versions.

Not recommended for production use yet. Please report issues at:
https://github.com/aop-protocol/aop/issues

## 🚀 Quick Start

See [README.md](README.md) for 5-minute quick start guide.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
```

5. **Check "This is a pre-release"** (for alpha/beta/rc)
6. Click **"Publish release"**

**Option B: Via GitHub CLI**

```bash
gh release create v0.1.0-alpha \
  --title "v0.1.0-alpha - Initial Alpha Release" \
  --notes-file release-notes.md \
  --prerelease
```

### 8. Publish to PyPI

**First time setup:**

```bash
# Install build tools
pip install build twine

# Create PyPI account at https://pypi.org/account/register/

# Create API token at https://pypi.org/manage/account/token/
# Save token securely
```

**Build and publish:**

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build distribution
python -m build

# Check build
twine check dist/*

# Upload to TestPyPI first (recommended for alpha)
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ aop

# If all good, upload to real PyPI
twine upload dist/*
```

**Verify on PyPI:**
- https://pypi.org/project/aop/

### 9. Announce Release

**Channels:**
- GitHub Discussions: https://github.com/aop-protocol/aop/discussions
- Twitter/LinkedIn (if applicable)
- Reddit: r/Python, r/MachineLearning
- Hacker News: Show HN (for major releases)
- Community forums (MCP, AI agent communities)

**Announcement Template:**

```markdown
🚀 AOP v0.1.0-alpha is here!

AOP (Agentic Observability Protocol) - Universal observability for AI agents.

✨ What's new:
- Complete event logging for MCP servers
- Web dashboard with live updates
- Export to 5 formats (JSON, CSV, TOON, OTEL, Prometheus)
- <1ms P99 overhead

📦 Install: pip install aop[cli,dashboard]
📚 Docs: https://github.com/aop-protocol/aop

⚠️ Alpha release - API may change. Feedback welcome!
```

---

## Managing Subsequent Releases

### Patch Release (0.1.1-alpha)

Bug fixes only, no new features:

```bash
# 1. Update version
vim pyproject.toml  # 0.1.0-alpha → 0.1.1-alpha

# 2. Update CHANGELOG
## [0.1.1-alpha] - 2025-01-20
### Fixed
- Fix database connection leak
- Fix dashboard refresh issue

# 3. Commit and tag
git commit -am "chore: Release v0.1.1-alpha"
git tag -a v0.1.1-alpha -m "Bug fix release"
git push && git push --tags

# 4. Publish to PyPI
python -m build
twine upload dist/*
```

### Minor Release (0.2.0-alpha)

New features, backward compatible:

```bash
# 1. Update version
vim pyproject.toml  # 0.1.0-alpha → 0.2.0-alpha

# 2. Update CHANGELOG
## [0.2.0-alpha] - 2025-02-01
### Added
- Batch insert API
- Redis storage backend
- Enhanced dashboard filters

# 3. Follow same process as above
```

### Moving to Beta

When features are complete and API is stabilizing:

```bash
# 0.1.0-alpha → 0.1.0-beta
vim pyproject.toml
vim CHANGELOG.md  # Add migration notes

git commit -am "chore: Release v0.1.0-beta"
git tag -a v0.1.0-beta -m "Beta release - API stabilizing"
git push && git push --tags
```

### Moving to Stable (1.0.0)

When ready for production:

```bash
# 0.1.0-beta → 1.0.0
vim pyproject.toml
vim CHANGELOG.md

# Add to CHANGELOG:
## [1.0.0] - 2025-03-01

**🎉 First stable release!**

### Changed
- API is now stable and will follow semantic versioning
- All features are production-ready

git commit -am "chore: Release v1.0.0 - First stable release"
git tag -a v1.0.0 -m "First stable release"
git push && git push --tags

# Publish to PyPI
python -m build
twine upload dist/*
```

---

## Automation (Future)

### GitHub Actions for Releases

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
```

---

## Hotfix Process

For critical bugs in production:

```bash
# 1. Create hotfix branch from tag
git checkout -b hotfix/0.1.1-alpha v0.1.0-alpha

# 2. Fix the bug
# ... make changes ...

# 3. Update version and changelog
vim pyproject.toml  # 0.1.0-alpha → 0.1.1-alpha
vim CHANGELOG.md

# 4. Commit and merge
git commit -am "fix: Critical bug in event logging"
git checkout main
git merge hotfix/0.1.1-alpha

# 5. Tag and release
git tag -a v0.1.1-alpha -m "Hotfix release"
git push && git push --tags

# 6. Publish to PyPI
python -m build
twine upload dist/*
```

---

## Best Practices

1. **Always test before releasing**
   - Run full test suite
   - Test installation from PyPI (TestPyPI first)
   - Test examples and documentation

2. **Keep CHANGELOG.md current**
   - Update as you develop, not just at release time
   - Use clear, user-focused language
   - Include migration notes for breaking changes

3. **Use conventional commits**
   - `feat:` for new features
   - `fix:` for bug fixes
   - `chore:` for releases and maintenance
   - `docs:` for documentation

4. **Tag properly**
   - Always use annotated tags (`git tag -a`)
   - Include release notes in tag message
   - Push tags explicitly (`git push --tags`)

5. **Communicate clearly**
   - Mark pre-releases clearly (alpha, beta, rc)
   - Document breaking changes
   - Provide migration guides
   - Announce releases

6. **Semantic versioning after 1.0.0**
   - Breaking changes = major bump
   - New features = minor bump
   - Bug fixes = patch bump

---

## Troubleshooting

### "Version already exists on PyPI"

You cannot re-upload the same version. Either:
- Bump to next version (0.1.1-alpha)
- Delete from TestPyPI and retry (not possible on PyPI)

### "Tag already exists"

Delete and recreate:
```bash
git tag -d v0.1.0-alpha
git push origin :refs/tags/v0.1.0-alpha
git tag -a v0.1.0-alpha -m "..."
git push origin v0.1.0-alpha
```

### "Build artifacts include test files"

Update `pyproject.toml`:
```toml
[tool.setuptools.packages.find]
exclude = ["tests*", "docs*"]
```

---

## Release Checklist Template

```markdown
## Release v0.1.0-alpha Checklist

- [ ] All tests pass
- [ ] Security scan passes
- [ ] Type checking passes
- [ ] Version updated in pyproject.toml
- [ ] CHANGELOG.md updated
- [ ] README.md accurate
- [ ] Examples tested
- [ ] Committed to main
- [ ] Tagged: git tag -a v0.1.0-alpha
- [ ] Pushed: git push --tags
- [ ] GitHub release created
- [ ] Built: python -m build
- [ ] Uploaded to TestPyPI
- [ ] Tested TestPyPI install
- [ ] Uploaded to PyPI
- [ ] Verified on PyPI
- [ ] Announced on GitHub Discussions
- [ ] Tweeted/posted (if applicable)
```

---

**Questions?** See [CONTRIBUTING.md](CONTRIBUTING.md) or open a [Discussion](https://github.com/aop-protocol/aop/discussions).

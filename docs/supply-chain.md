# Supply Chain Security (Series 22.4)

Free, open-source dependency and code security controls for the learning engine.

## Dependency Management

### Version Pinning Strategy

All Python dependencies are pinned in `backend/requirements.txt` to exact versions:

```
fastapi==0.143.0
sqlalchemy[asyncio]==2.1.4
asyncpg==0.32.0
# ... all other deps pinned
```

**Update Cadence**: Quarterly (Q1, Q2, Q3, Q4) or on urgent security patches.

**Process**:
1. Run `pip list --outdated` to check available updates
2. Update `backend/requirements.txt` with new versions
3. Test locally: `pytest tests/ -v`
4. Test with the local gate: `scripts/ci_local.sh` (GitHub Actions has had no runner since 2026-10-01, H.13)
5. The owner merges to master (ADR-45), which auto-deploys to production (Railway)

### Automated Dependency Scanning

**Dependabot** — configuration in `.github/dependabot.yml` (added 2026-09-25): weekly
version updates for `backend/` (pip) and `frontend/` (npm), monthly for GitHub Actions,
minor/patch grouped. *Not verified:* whether Dependabot security alerts are enabled in the
repository settings (owner-only), and whether GitHub runs the jobs given the billing block
on Actions (H.13/H.17). Until the 2026-09-25 file existed, this section claimed Dependabot
was enabled; nothing in the repo configured it.
- PR description includes CVE details and remediation guidance

**Status**: Check `.github/dependabot.yml` for current configuration. Currently scoped to `backend/requirements.txt` and `frontend/package.json`.

## Pre-Commit Hooks

Install via:
```bash
pip install pre-commit
pre-commit install
```

Hooks run on every `git commit`:
- **gitleaks**: Prevents committing secrets (API keys, credentials, tokens)
- **bandit**: Detects Python security issues (hardcoded passwords, SQL injection patterns, insecure randomness)
- **semgrep**: Pattern-based SAST against OWASP Top 10 and CWE rules
- **ruff**: Code formatting and linting (also runs in CI)
- **yamllint**: YAML config validation

Run manually anytime:
```bash
pre-commit run --all-files
```

## SBOM (Software Bill of Materials)

Generate CycloneDX JSON SBOMs before release using the automated script:

```bash
# Automatically generates SBOMs for Python (backend) and Node.js (frontend)
bash scripts/generate_sbom.sh
```

This generates:
- `sbom/sbom-python.json` — Inventory of Python dependencies from `backend/requirements.txt`
- `sbom/sbom-nodejs.json` — Inventory of Node.js dependencies from `frontend/package-lock.json` (if npm is available)

Output files contain machine-readable inventory of all dependencies, versions, and license metadata. Used by security scanners and compliance audits.

**Setup**: `cyclonedx-bom` is pinned in `backend/requirements.txt` (v7.5.0). The script installs it if missing and uses the `cyclonedx-py` CLI tool.

**When to generate**: Before each production release (see `docs/RELEASE.md`). CI/CD pipelines should run this and commit or archive the SBOMs as build artifacts.

**Limitations**: 
- Node.js SBOM generation (`cyclonedx-npm`) is not currently available due to package availability issues. Python SBOM generation is reliable and required.
- For Node.js, you can manually inspect `frontend/package-lock.json` or use other npm-based SBOM tools if needed.

## Artifact Registry Check

**GitHub Actions CI** includes a dependency audit step:
```yaml
- name: Dependency audit (pip-audit)
  run: pip-audit --progress-spinner off
```

This runs on every PR and push to master. Known CVEs are tracked in `.github/workflows/ci.yml` under `--ignore-vuln` flags (documented with reason why we accept the risk).

**Current ignored CVEs** (as of 2026-09-19):
- PYSEC-2026-161, PYSEC-2026-248, etc. — Starlette/FastAPI upstream issues (major upgrade deferred to 7.1 security audit)

## Environment Secrets

**Never commit**:
- `.env` files
- Private keys or certificates
- API keys (Groq, Stripe, AWS, etc.)
- Database credentials

All secrets are stored in:
- **Local**: `.env.example` template (no secrets) + local `.env` (gitignored)
- **CI/CD**: GitHub Secrets or Railway environment variables
- **Production**: Railway dashboard or deployment pipeline

Verify via:
```bash
git diff HEAD -- .env  # Should be empty or not tracked
grep -r "PRIVATE_KEY\|API_KEY\|SECRET" .env  # Should find nothing
```

## Checklist

- [ ] `.pre-commit-config.yaml` installed and hooks running locally
- [ ] `pip install pre-commit && pre-commit install` in local clone
- [ ] Dependabot enabled in GitHub (repository settings → Code security → Dependabot)
- [ ] CI pipeline runs `pip-audit` on every push (verify in `.github/workflows/ci.yml`)
- [ ] Requirements.txt pinned to exact versions (no `>=`, `~=`, `*`)
- [ ] SBOM generation script configured: `bash scripts/generate_sbom.sh`
- [ ] `cyclonedx-bom` in `backend/requirements.txt` for Python SBOM generation
- [ ] SBOMs generated before each production release
- [ ] `.env` and secrets are gitignored (check `.gitignore`)
- [ ] No API keys hardcoded in the codebase (run `gitleaks detect -v` locally)
- [ ] `sbom/` directory added to `.gitignore` (generated artifacts, not source)

## Integration with CI/CD

All security checks run in GitHub Actions before deployment:

1. **Dependency Audit** (`pip-audit`): Blocks build if unacknowledged CVEs found
2. **Pre-commit Hooks** (via Ruff, bandit, etc.): Linting and security patterns
3. **Tests** (pytest): Functional correctness and integration tests
4. **Type Check** (mypy): Type safety for Python code

**Not true today:** a commit reaching `master` deploys (Railway and Cloudflare Pages) whether
or not these checks ran — GitHub CI does not run (H.13/H.17). What stands in between is the
local gate (`.githooks/pre-push` level 1, blocking; `scripts/ci_local.sh` level 2, not
blocking) and the owner merging by hand (ADR-45).

## Monitoring & Response

**If a vulnerability is discovered**:
1. Check if it's already tracked in `.github/workflows/ci.yml` (may be an accepted risk)
2. If new: create a GitHub issue or PR
3. Update the vulnerable package to a patched version
4. Run tests locally and in CI to verify the fix
5. The owner merges (ADR-45); master deploys automatically to production

**Resource**: [CVE Details](https://www.cvedetails.com), [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/), [Snyk](https://snyk.io)

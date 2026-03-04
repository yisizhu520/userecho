# Security Policy

## Supported Versions

We actively maintain security fixes for the following versions:

| Version | Supported |
|---------|-----------|
| latest (main branch) | ✅ |
| older releases | ❌ |

## Reporting a Vulnerability

**请勿**通过公开的 GitHub Issue 报告安全漏洞。

If you discover a security vulnerability, **do not** open a public GitHub Issue.

### How to Report

Please send a detailed report to: **security@userecho.app**

Include the following in your report:

1. **Description** — A clear description of the vulnerability
2. **Impact** — What could an attacker do by exploiting this?
3. **Reproduction Steps** — Step-by-step instructions to reproduce the issue
4. **Affected Component** — Which part of the codebase is affected (frontend / backend / deploy config)
5. **Suggested Fix** (optional) — If you have a fix in mind

### What to Expect

- We will acknowledge your report within **3 business days**
- We aim to release a fix within **14 days** for critical issues, **30 days** for others
- We will credit you in the release notes (unless you prefer to remain anonymous)

### Scope

Issues in scope include:

- SQL Injection, XSS, CSRF
- Authentication or authorization bypass
- Sensitive data exposure (API keys, credentials, personal data)
- Remote Code Execution (RCE)
- Server-Side Request Forgery (SSRF)
- Insecure default configuration in shipped Docker images

Out of scope:

- Vulnerabilities in third-party dependencies (please report those upstream)
- Issues requiring physical access to the server
- Social engineering attacks

## Security Best Practices for Self-Hosting

When deploying userecho yourself, please follow these guidelines:

1. **Never commit `.env` files** containing real credentials to version control
2. **Use strong, randomly generated** `TOKEN_SECRET_KEY` and `OPERA_LOG_ENCRYPT_SECRET_KEY`
3. **Restrict database access** — PostgreSQL should not be exposed to the public internet
4. **Enable HTTPS** — Use a reverse proxy (Nginx) with valid TLS certificates
5. **Rotate API keys** regularly for AI providers
6. **Keep dependencies updated** — Run `uv sync` and `pnpm install` regularly

## Vulnerability Disclosure Policy

We follow a responsible disclosure policy. Once a fix is released, we will:

1. Publish a security advisory on GitHub
2. Add an entry to the CHANGELOG
3. Credit the reporter (with permission)

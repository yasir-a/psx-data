# Security Policy

## Supported Versions

At this stage of the project, only the latest version of `psx-data` is actively supported with security fixes.

| Version | Supported |
| ------- | --------- |
| Latest  | Yes       |
| Older versions | No    |

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues.

If you believe you have discovered a security vulnerability in psx-data, please report it privately through GitHub's security reporting features, if enabled for the repository.

When reporting a vulnerability, please provide:

- A description of the vulnerability
- The affected component or file
- Steps to reproduce the issue
- The potential impact
- Any proof-of-concept code or relevant logs
- A suggested mitigation, if available

Please allow the maintainers reasonable time to investigate and address the issue before publicly disclosing it.

## What to Report

Examples of security issues include:

- Authentication or authorization vulnerabilities
- Exposure of credentials, tokens, or other secrets
- Unsafe handling of external data
- Injection vulnerabilities
- Arbitrary code execution
- Dependency-related security vulnerabilities
- Vulnerabilities that could compromise a user's system or data

## Security Best Practices for Contributors

Contributors should:

- Never commit passwords, API keys, tokens, or other secrets.
- Avoid including sensitive information in issues, pull requests, or logs.
- Validate and safely handle data obtained from external sources.
- Keep dependencies to a minimum.
- Report suspected vulnerabilities privately rather than publicly.

## Disclosure

Once a vulnerability has been investigated and an appropriate fix is available, the maintainers may publish a security advisory describing the issue, its impact, and the affected versions.

The timing and contents of any public disclosure will depend on the severity of the vulnerability and the availability of a fix.
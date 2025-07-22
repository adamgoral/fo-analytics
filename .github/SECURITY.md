# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of FO Analytics seriously. If you believe you have found a security vulnerability, please report it to us as described below.

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to security@fo-analytics.com.

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

## Preferred Languages

We prefer all communications to be in English.

## Policy

We follow the principle of Coordinated Vulnerability Disclosure.

## Security Best Practices

### For Contributors

1. **Never commit sensitive data**
   - API keys, passwords, or tokens
   - Customer data or PII
   - Internal URLs or infrastructure details

2. **Dependencies**
   - Keep dependencies up to date
   - Review security advisories
   - Use tools like `npm audit` and `pip-audit`

3. **Code Review**
   - All code must be reviewed before merging
   - Pay special attention to:
     - Authentication and authorization
     - Input validation
     - SQL queries
     - File operations
     - External API calls

4. **Testing**
   - Write security tests for sensitive features
   - Test for common vulnerabilities
   - Use static analysis tools

### Security Headers

Our application implements the following security headers:
- Content-Security-Policy
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Strict-Transport-Security

### Data Protection

- All data in transit is encrypted using TLS 1.2+
- Sensitive data at rest is encrypted
- PII is handled according to GDPR/CCPA requirements
- Regular security audits and penetration testing
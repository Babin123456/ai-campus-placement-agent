# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in the AI Campus Placement Agent, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, report the issue privately using [GitHub Security Advisories](https://github.com/deepikagandla74/ai-campus-placement-agent/security/advisories/new).

Include the following information in your report:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- Any suggested fixes or mitigations (if available)

### What to Expect

- We will acknowledge receipt of your report within 48 hours
- We will provide a detailed response within 7 days
- We will work with you to understand and validate the issue
- We will coordinate a fix and release plan
- We will credit you in the security advisory (unless you prefer to remain anonymous)

### Security Best Practices

When using this application:

1. **Keep API Keys Secure**: Never commit `.env` files or API keys to version control
2. **Use Environment Variables**: Always use environment variables for sensitive configuration
3. **Regular Updates**: Keep dependencies updated to receive security patches
4. **Secure Deployment**: Use HTTPS in production and configure proper CORS policies
5. **Input Validation**: The application includes input validation, but ensure proper deployment security

### Known Security Considerations

- **API Key Management**: Users must provide their own Gemini API key via environment variables
- **File Uploads**: PDF uploads are validated and restricted to `.pdf` extensions
- **Database**: SQLite is used for development. For production, consider PostgreSQL or MySQL with proper authentication
- **Session Management**: Flask secret keys should be set to strong, random values in production

### Dependency Management

We regularly update dependencies to address security vulnerabilities. To check for updates:

```bash
pip list --outdated
pip install --upgrade [package-name]
```

For automated dependency scanning, consider using tools like:
- `safety` (Python package vulnerability scanner)
- `pip-audit` (Audits Python dependencies for known vulnerabilities)
- `bandit` (Finds common security issues in Python code)

### Security Resources

- [OWASP Python Security](https://owasp.org/www-project-python-security/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [Python Security Documentation](https://docs.python.org/3/library/security_warnings.html)

Thank you for helping keep the AI Campus Placement Agent and its users safe!

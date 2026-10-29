# Support

Need help with the AI Campus Placement Agent? Here are the best ways to get support.

## Documentation

First, check our comprehensive documentation:

- 📖 [README.md](README.md) - Project overview, features, and getting started guide
- 📝 [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute to the project
- 🔒 [SECURITY.md](SECURITY.md) - Security policy and vulnerability reporting

## Community Support

### GitHub Issues
- 🐛 [Issue Tracker](https://github.com/deepikagandla74/ai-campus-placement-agent/issues) - Report bugs and request features
- Before creating an issue:
  1. Search existing issues to avoid duplicates
  2. Check whether an existing issue already answers your question
  3. Use the appropriate issue template (Bug Report or Feature Request)

## Getting Help

### Before Asking for Help

1. **Read the Documentation**: Most common questions are answered in the README
2. **Search First**: Check existing [Issues](https://github.com/deepikagandla74/ai-campus-placement-agent/issues)
3. **Provide Context**: When asking for help, include:
   - Your operating system and version
   - Python version (`python --version`)
   - Steps to reproduce the issue
   - Error messages or stack traces
   - What you expected to happen vs. what actually happened

### How to Ask a Good Question

When asking for help, follow these guidelines:

✅ **Do:**
- Be specific and clear about your problem
- Share relevant code snippets (formatted properly)
- Include error messages and stack traces
- Mention what you've already tried
- Use a descriptive title

❌ **Don't:**
- Say "it doesn't work" without details
- Post screenshots of code (copy-paste instead)
- Ask questions already answered in documentation
- Use all caps or excessive punctuation
- Be rude or demanding

## Common Issues

### Installation Problems

**Problem**: `pip install` fails
- **Solution**: Ensure you have Python 3.9+ installed
- Try: `pip install --upgrade pip` before installing requirements

### API Key Issues

**Problem**: "Invalid API Key" error
- **Solution**: 
  1. Check your `.env` file has the correct `GEMINI_API_KEY`
  2. Get a free API key from [Google AI Studio](https://ai.google.dev/)
  3. Ensure the key has no extra spaces or quotes

### PDF Upload Issues

**Problem**: Resume upload fails
- **Solution**:
  1. Ensure the file is a valid PDF
  2. Check file size is reasonable (< 10MB)
  3. Verify the `uploads/` directory exists and is writable

### Database Errors

**Problem**: SQLite database errors
- **Solution**:
  1. Delete `placement_agent.db` and restart the app
  2. Ensure write permissions on the project directory
  3. Check SQLite is installed: `python -c "import sqlite3"`

## Reporting Bugs

If you find a bug, please:

1. Check if it's already reported in [Issues](https://github.com/deepikagandla74/ai-campus-placement-agent/issues)
2. Create a new issue using the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
3. Include:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or error messages

## Feature Requests

Have an idea for improvement?

1. Check existing [Issues](https://github.com/deepikagandla74/ai-campus-placement-agent/issues) first
2. Create a new issue using the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md)
3. Describe:
   - The feature you want
   - Why it would be useful
   - How you envision it working
   - Any alternatives you considered

## Contributing

Want to contribute code? See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support expectations

- Support is community-driven through GitHub Issues. Please do not include API keys, private resumes, or other sensitive data in public posts.
- For security concerns, follow the private reporting instructions in [SECURITY.md](SECURITY.md).

## Code of Conduct

Please be respectful and follow our [Code of Conduct](CODE_OF_CONDUCT.md) in all interactions.

---

Thank you for using AI Campus Placement Agent! We're here to help you succeed. 🚀

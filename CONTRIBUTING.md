# Contributing to AI Campus Placement Agent

Thank you for your interest in contributing to the AI Campus Placement Agent! We welcome contributions from the community to help improve this open-source project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/ai-campus-placement-agent.git
   cd ai-campus-placement-agent
   ```

## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix/MacOS:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `.env.example` (if available) or create a `.env` file
   - Add your Gemini API key:
     ```
     FLASK_SECRET_KEY=your_secret_key_here
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Visit `http://127.0.0.1:5000/` in your browser

## Contributing Guidelines

### What Can I Contribute?

We welcome contributions in the following areas:

- **Bug fixes**: Help us squash bugs and improve stability
- **New features**: Propose and implement new placement-related features
- **Documentation**: Improve documentation, add examples, or write tutorials
- **UI/UX improvements**: Enhance the user interface and experience
- **Performance optimizations**: Make the application faster and more efficient
- **Test coverage**: Add tests to improve code reliability

### Development Workflow

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bugfix-name
   ```

2. Make your changes following our coding standards:
   - Follow PEP 8 style guidelines
   - Write clear, descriptive commit messages
   - Add comments for complex logic
   - Update relevant documentation

3. Test your changes thoroughly:
   - Ensure the application runs without errors
   - Test the specific feature you modified
   - Check for regressions in existing functionality

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Brief description of your changes"
   ```

### Coding Standards

- **Python**: Follow PEP 8 style guide
- **HTML/CSS/JS**: Follow modern best practices
- **Comments**: Add docstrings to functions and classes
- **Variable naming**: Use descriptive, meaningful names
- **Error handling**: Include proper error handling and logging

## Pull Request Process

1. **Update Documentation**: If your changes affect functionality, update the README or relevant documentation

2. **Commit Messages**: Use clear, descriptive commit messages:
   - `feat: add new interview evaluation feature`
   - `fix: resolve PDF parsing error for certain formats`
   - `docs: update installation instructions`
   - `refactor: simplify database initialization`

3. **Push to Your Fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**:
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill out the PR template with details about your changes
   - Link related issues using `#issue-number`

5. **Review Process**:
   - Maintainers will review your PR
   - Address any feedback or requested changes
   - Once approved, your PR will be merged

### PR Checklist

Before submitting your PR, ensure:

- [ ] Code follows the project's style guidelines
- [ ] Changes are tested and working
- [ ] Documentation is updated if needed
- [ ] Commit messages are clear and descriptive
- [ ] No merge conflicts with the main branch
- [ ] PR description explains the "why" and "what" of changes

## Reporting Issues

### Bug Reports

When reporting a bug, please include:

- **Title**: Clear, descriptive bug title
- **Description**: Detailed explanation of the bug
- **Steps to Reproduce**: Clear steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Screenshots**: If applicable, add screenshots
- **Environment**:
  - OS: [e.g., Windows 10, macOS, Ubuntu]
  - Python version: [e.g., 3.9.7]
  - Browser: [e.g., Chrome 95]

### Feature Requests

For feature requests, please include:

- **Title**: Clear feature title
- **Description**: Detailed description of the feature
- **Use Case**: Why this feature would be useful
- **Proposed Solution**: How you envision the feature working
- **Alternatives**: Any alternative solutions considered

## Questions

If you have questions about contributing:

- Check existing [Issues](https://github.com/your-username/ai-campus-placement-agent/issues)
- Start a [Discussion](https://github.com/your-username/ai-campus-placement-agent/discussions)
- Contact maintainers through the repository

## Recognition

Contributors will be recognized in the project's CONTRIBUTORS file and README.

Thank you for contributing to AI Campus Placement Agent! 🚀

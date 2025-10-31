# Contributing to SynthAIx

Thank you for your interest in contributing to SynthAIx! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. Use the bug report template
3. Include:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Python version, Docker version)
   - Logs if applicable

### Suggesting Features

1. Check if the feature has already been suggested
2. Use the feature request template
3. Explain:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative solutions considered
   - Additional context

### Pull Requests

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/synthaix.git
   cd synthaix
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   ./setup-dev.sh
   ```

4. **Make your changes**
   - Write clear, documented code
   - Follow the existing code style
   - Add tests for new features
   - Update documentation as needed

5. **Run tests**
   ```bash
   # Backend tests
   cd backend
   source venv/bin/activate
   pytest
   
   # Frontend tests
   cd ../frontend
   source venv/bin/activate
   pytest
   ```

6. **Format code**
   ```bash
   black backend/app frontend/
   ```

7. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   Use conventional commits:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes
   - `refactor:` Code refactoring
   - `test:` Test changes
   - `chore:` Build/tooling changes

8. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub

## Development Guidelines

### Code Style

- **Python**: Follow PEP 8
- **Line length**: 100 characters max
- **Docstrings**: Use Google style
- **Type hints**: Use where appropriate

Example:
```python
def generate_data(
    schema: DataSchema, 
    total_rows: int
) -> List[Dict[str, Any]]:
    """
    Generate synthetic data based on schema.
    
    Args:
        schema: Data schema definition
        total_rows: Number of rows to generate
        
    Returns:
        List of generated data rows
        
    Raises:
        ValueError: If schema is invalid
    """
    pass
```

### Testing

- Write tests for new features
- Maintain test coverage > 80%
- Use pytest fixtures for common setup
- Mock external API calls

### Documentation

- Update README.md if adding features
- Add docstrings to all functions/classes
- Update API.md for API changes
- Include examples where helpful

## Project Structure

```
synthaix/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── agents/   # AI agents
│   │   ├── api/      # API routes
│   │   ├── core/     # Core config
│   │   ├── models/   # Data models
│   │   ├── tools/    # AI tools
│   │   └── utils/    # Utilities
│   └── tests/        # Backend tests
├── frontend/         # Streamlit frontend
│   ├── components/   # UI components
│   ├── utils/        # Frontend utils
│   └── tests/        # Frontend tests
└── docs/            # Documentation
```

## Architecture Principles

1. **Separation of Concerns**: Keep business logic separate from API routes
2. **Dependency Injection**: Use FastAPI's dependency injection
3. **Type Safety**: Use Pydantic models for validation
4. **Error Handling**: Proper exception handling and logging
5. **Scalability**: Design for horizontal scaling
6. **Testing**: Write testable, modular code

## Adding New Features

### Adding a New Field Type

1. Add to `FieldType` enum in `backend/app/models/schemas.py`
2. Update generator prompt in `backend/app/agents/generator.py`
3. Add validation logic if needed
4. Update documentation
5. Add tests

### Adding a New API Endpoint

1. Define route in `backend/app/api/routes.py`
2. Create request/response models in `backend/app/models/schemas.py`
3. Implement business logic
4. Add error handling
5. Update API.md documentation
6. Write tests

### Adding Frontend Features

1. Create component in `frontend/components/`
2. Update main app in `frontend/app.py`
3. Add API client methods if needed
4. Test UI flow
5. Update documentation

## Review Process

1. **Automated checks**: CI/CD runs tests and linting
2. **Code review**: Maintainer reviews code quality
3. **Testing**: Verify tests pass and coverage is adequate
4. **Documentation**: Ensure docs are updated
5. **Approval**: Get approval from maintainer
6. **Merge**: Squash and merge to main

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Chat**: Join our Discord (link in README)
- **Issues**: Create a GitHub Issue

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Annual contributor highlights

Thank you for contributing to SynthAIx! 🚀

# Contributing to Nostalgia TV

Thank you for your interest in contributing to **Nostalgia TV**! We welcome contributions from developers, retro-enthusiasts, designers, and hobbyists.

---

## Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## How Can I Contribute?

### 1. Reporting Bugs
- Check the [GitHub Issues](https://github.com/bgenome/nostalgia-tv/issues) to verify if the bug has already been reported.
- If not, open a new issue using the **Bug Report** template.
- Include your operating system, browser version (if using Web TV), Python version, and reproducible steps or logs.

### 2. Suggesting Features
- Open an issue using the **Feature Request** template.
- Describe the feature, why it adds nostalgic value or utility, and any proposed implementation details.

### 3. Pull Requests
1. **Fork** the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/my-cool-feature
   ```
2. **Make your changes**. Keep changes focused and self-contained.
3. **Run the test suite**:
   ```bash
   python3 -m unittest discover -s tests -v
   ```
4. **Follow code style**:
   - Python code follows PEP 8 conventions.
   - Core server files (`server.py`) must maintain **zero external pip dependencies** so it remains lightweight and portable.
   - For desktop kiosk additions (`src/ui/`), ensure backwards compatibility with PyQt6.
5. **Commit your changes**:
   - Use clear, conventional commit messages: `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`.
6. **Push and open a Pull Request**:
   - Fill out the PR template with a description of changes and testing proof.

---

## Local Development Setup

### Running the Web Broadcast Server (Zero Dependencies)
```bash
python3 server.py
# Open http://localhost:8080 (Web TV)
# Open http://localhost:8080/admin (Station Control Console)
```

### Running Native Desktop Kiosk (Requires PyQt6)
```bash
pip install -r requirements.txt
python3 main.py
```

### Running Tests
```bash
python3 -m unittest discover -s tests -v
# or with pytest
pytest tests/ -v
```

---

## Questions or Support?
Feel free to open an issue or discussion on GitHub. Happy retro broadcasting!

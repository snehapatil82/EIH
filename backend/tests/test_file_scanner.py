import tempfile
from pathlib import Path
from app.repository.file_scanner import FileScanner

def test_file_scanner_ignore_rules():
    scanner = FileScanner()
    
    # Test ignored directories
    assert scanner.should_ignore(Path("app/.git/config"), Path(".git/config")) is True
    assert scanner.should_ignore(Path("node_modules/pkg/index.js"), Path("node_modules/pkg/index.js")) is True
    assert scanner.should_ignore(Path("app/__pycache__/main.cpython-310.pyc"), Path("__pycache__/main.cpython-310.pyc")) is True
    assert scanner.should_ignore(Path(".env"), Path(".env")) is True

    # Test allowed source files
    assert scanner.should_ignore(Path("src/main.py"), Path("src/main.py")) is False
    assert scanner.should_ignore(Path("README.md"), Path("README.md")) is False

def test_language_detection():
    scanner = FileScanner()
    assert scanner.detect_language(Path("main.py")) == "Python"
    assert scanner.detect_language(Path("App.tsx")) == "TypeScript (React)"
    assert scanner.detect_language(Path("server.go")) == "Go"
    assert scanner.detect_language(Path("Dockerfile")) == "Dockerfile"
    assert scanner.detect_language(Path("README.md")) == "Markdown"

def test_scan_repository_counts():
    scanner = FileScanner()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create sample files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "sample.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")
        (tmp_path / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "dummy.txt").write_text("ignore me", encoding="utf-8")

        files, stats, total_f, total_l = scanner.scan_repository(tmp_path)
        assert total_f == 2
        assert total_l == 3 # 2 in py + 1 in md
        assert "Python" in stats

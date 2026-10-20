"""Throwaway git repositories for the scripts/ tests.

The instruments under test read a REVISION through git, never a working tree,
so the only honest fixture is a real commit. Line-ending conversion is pinned
off so the bytes committed are the bytes written, on every platform.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

_GIT = ["git", "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false",
        "-c", "user.name=test", "-c", "user.email=test@example.invalid"]


class GitRepo:
    def __init__(self, files):
        self.path = Path(tempfile.mkdtemp(prefix="scripts-test-"))
        self.git("init", "-q")
        for rel, text in files.items():
            target = self.path / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.encode("utf-8"))
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "fixture")
        self.head = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.run([*_GIT, *args], cwd=self.path, check=True,
                              capture_output=True, text=True).stdout

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)

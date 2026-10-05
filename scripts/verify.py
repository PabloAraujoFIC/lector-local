import subprocess
import sys


def main():
    commands = [
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "-m", "ruff", "check", "core", "scripts", "tests"],
        [sys.executable, "-m", "mypy", "core"],
        ["npm.cmd" if sys.platform == "win32" else "npm", "run", "typecheck"],
        ["npm.cmd" if sys.platform == "win32" else "npm", "run", "lint"],
        ["npm.cmd" if sys.platform == "win32" else "npm", "test"],
        ["npm.cmd" if sys.platform == "win32" else "npm", "run", "build"],
    ]
    for command in commands:
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()

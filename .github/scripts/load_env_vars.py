#!/usr/bin/env python3
"""Load environment variables from project.env for GitHub Actions and gcloud."""

import os
import sys
from pathlib import Path


def parse_env_file(env_path: Path) -> dict[str, str]:
    """Parse a .env file into a dictionary."""
    if not env_path.is_file():
        raise FileNotFoundError(f"Missing {env_path}")

    lines = env_path.read_text(encoding="utf-8").splitlines()
    pairs = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            parts = line.split("=", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                # Remove surrounding quotes
                if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                    value = value[1:-1]
                if key:
                    pairs.append((key, value))
    return dict(pairs)


def write_to_github_env(env_vars: dict[str, str]) -> None:
    """Write variables to GITHUB_ENV for subsequent steps."""
    github_env_path = os.environ.get("GITHUB_ENV")
    if not github_env_path:
        print("Warning: GITHUB_ENV not set. Cannot export variables.")
        return

    path = Path(github_env_path)
    try:
        with path.open("a", encoding="utf-8") as f:
            for k, v in env_vars.items():
                if "\n" in v:
                    delimiter = f"EOF_{k}_{os.urandom(4).hex()}"
                    f.write(f"{k}<<{delimiter}\n{v}\n{delimiter}\n")
                else:
                    f.write(f"{k}={v}\n")
    except OSError as e:
        print(f"Error writing to GITHUB_ENV: {e}")


def write_gcloud_env_string_to_output(env_vars: dict[str, str]) -> None:
    """Write comma-separated KEY=VALUE string for gcloud --set-env-vars."""
    github_output_path = os.environ.get("GITHUB_OUTPUT")
    if not github_output_path:
        print("Warning: GITHUB_OUTPUT not set.")
        return

    gcloud_env_string = ",".join(f"{k}={v}" for k, v in env_vars.items())

    path = Path(github_output_path)
    try:
        with path.open("a", encoding="utf-8") as f:
            delimiter = f"EOF_GCLOUD_ENV_{os.urandom(4).hex()}"
            f.write(f"gcloud_env_string<<{delimiter}\n{gcloud_env_string}\n{delimiter}\n")
            f.write("gcloud_vars_generated=true\n")
    except OSError as e:
        print(f"Error writing to GITHUB_OUTPUT: {e}")


def main() -> None:
    """Main entry point."""
    env_file = sys.argv[1] if len(sys.argv) > 1 else "project.env"
    env_path = Path(env_file)

    try:
        if env_vars := parse_env_file(env_path):
            write_to_github_env(env_vars)
            write_gcloud_env_string_to_output(env_vars)
            print(f"Processed {len(env_vars)} variables from {env_path}")
        else:
            print(f"No variables found in {env_path}")
            write_gcloud_env_string_to_output({})
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

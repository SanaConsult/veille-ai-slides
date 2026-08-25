#!/usr/bin/env python3
"""
Refreshes the Instagram long-lived token ONCE per workflow run and exposes it
to later steps via $GITHUB_ENV (as IG_ACCESS_TOKEN_FRESH), masking it in logs.
Both the carousel and the Reel publish steps reuse this single fresh token
instead of each refreshing independently (refreshing twice in one run is
wasteful and would invalidate the first refreshed token).

Requires env var IG_ACCESS_TOKEN. Must run with GITHUB_ENV pointing at a
writable file (true inside GitHub Actions).
"""
import os
import sys

from ig_common import refresh_token


def main():
    token = os.environ["IG_ACCESS_TOKEN"]
    new_token = refresh_token(token)

    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as f:
            f.write(f"IG_ACCESS_TOKEN_FRESH={new_token}\n")
    # Mask the fresh token in any subsequent log output.
    print(f"::add-mask::{new_token}")
    print("Refreshed Instagram token.", file=sys.stderr)


if __name__ == "__main__":
    main()

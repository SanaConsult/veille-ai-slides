#!/usr/bin/env python3
"""
Persists this run's refreshed Instagram token back into the repo's
IG_ACCESS_TOKEN GitHub Actions secret, so tomorrow's run picks it up.
Runs once, after both publish_carousel.py and publish_reel.py succeed.

Required env vars: IG_ACCESS_TOKEN_FRESH, GITHUB_REPOSITORY.
Optional: GH_SECRETS_PAT (a PAT with Contents:read + Secrets:read&write on
this repo). If unset, this is a no-op — next run reuses the old token until
someone updates the secret manually or configures GH_SECRETS_PAT.
"""
import os
import sys

from ig_common import update_secret


def main():
    new_token = os.environ["IG_ACCESS_TOKEN_FRESH"]
    repo = os.environ["GITHUB_REPOSITORY"]
    pat = os.environ.get("GH_SECRETS_PAT")

    if not pat:
        print(
            "WARN: GH_SECRETS_PAT not set — refreshed token was NOT persisted. "
            "Next run will reuse the old token.",
            file=sys.stderr,
        )
        return

    print("Persisting refreshed token to repo secret IG_ACCESS_TOKEN...")
    update_secret(repo, pat, "IG_ACCESS_TOKEN", new_token)
    print("Done.")


if __name__ == "__main__":
    main()

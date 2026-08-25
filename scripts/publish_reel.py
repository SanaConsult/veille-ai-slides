#!/usr/bin/env python3
"""
Publishes the day's Reel video (reel.mp4, already pushed to the repo under
slides/<date>/) to Instagram, using the same already-refreshed access token
as publish_carousel.py (see refresh_ig_token.py).

Required env vars:
  IG_ACCESS_TOKEN_FRESH   token from refresh_ig_token.py this run
  IG_USER_ID              Instagram Business/Login user id
  GITHUB_REPOSITORY       owner/repo (set automatically by GitHub Actions)
  SLIDE_DATE              YYYY-MM-DD folder name under slides/
  CONTENT_JSON_PATH       path to today's content.json (default: content.json)
"""
import json
import os
import sys

import requests
from ig_common import GRAPH, build_caption, cdn_url, get_permalink, publish_container, wait_finished, wait_for_cdn


def create_reel_container(user_id, token, video_url, caption, share_to_feed=True):
    r = requests.post(
        f"{GRAPH}/{user_id}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption,
            "share_to_feed": "true" if share_to_feed else "false",
            "access_token": token,
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["id"]


def main():
    token = os.environ["IG_ACCESS_TOKEN_FRESH"]
    user_id = os.environ["IG_USER_ID"]
    repo = os.environ["GITHUB_REPOSITORY"]
    date = os.environ["SLIDE_DATE"]
    content_path = os.environ.get("CONTENT_JSON_PATH", "content.json")

    with open(content_path, encoding="utf-8") as f:
        content = json.load(f)

    print("Waiting for the Reel video to be reachable via CDN...")
    video_url = cdn_url(repo, date, "reel.mp4")
    if not wait_for_cdn(video_url):
        print(f"ERROR: {video_url} never became reachable", file=sys.stderr)
        sys.exit(1)

    caption = build_caption(content)
    print("Creating Reel container...")
    creation_id = create_reel_container(user_id, token, video_url, caption)

    print("Waiting for video processing (can take longer than images)...")
    if not wait_finished(creation_id, token, tries=20, delay=10):
        print("ERROR: Reel did not reach FINISHED status in time", file=sys.stderr)
        sys.exit(1)

    print("Publishing...")
    media_id = publish_container(user_id, token, creation_id)
    permalink = get_permalink(media_id, token)
    print(f"Published Reel: {permalink}")


if __name__ == "__main__":
    main()

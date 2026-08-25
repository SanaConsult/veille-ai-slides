#!/usr/bin/env python3
"""
Publishes the day's 5-slide image carousel to Instagram, using an already
-refreshed access token (see refresh_ig_token.py — run once per workflow,
shared with publish_reel.py).

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
import time

import requests
from ig_common import GRAPH, build_caption, cdn_url, get_permalink, publish_container, wait_finished, wait_for_cdn


def create_carousel_item(user_id, token, image_url, tries=3):
    last_err = None
    for _ in range(tries):
        r = requests.post(
            f"{GRAPH}/{user_id}/media",
            data={"image_url": image_url, "is_carousel_item": "true", "access_token": token},
            timeout=60,
        )
        if r.ok:
            return r.json()["id"]
        last_err = r.text
        time.sleep(5)
    raise RuntimeError(f"Failed to create carousel item for {image_url}: {last_err}")


def create_carousel_container(user_id, token, children, caption):
    r = requests.post(
        f"{GRAPH}/{user_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "caption": caption,
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

    print("Waiting for slides to be reachable via CDN...")
    first_url = cdn_url(repo, date, "slide-1.png")
    if not wait_for_cdn(first_url):
        print(f"ERROR: {first_url} never became reachable", file=sys.stderr)
        sys.exit(1)

    print("Creating carousel items...")
    children = []
    for i in range(1, 6):
        url = cdn_url(repo, date, f"slide-{i}.png")
        cid = create_carousel_item(user_id, token, url)
        children.append(cid)
        print(f"  slide-{i}: {cid}")

    caption = build_caption(content)
    print("Creating carousel container...")
    creation_id = create_carousel_container(user_id, token, children, caption)

    print("Waiting for processing...")
    if not wait_finished(creation_id, token):
        print("ERROR: carousel did not reach FINISHED status in time", file=sys.stderr)
        sys.exit(1)

    print("Publishing...")
    media_id = publish_container(user_id, token, creation_id)
    permalink = get_permalink(media_id, token)
    print(f"Published carousel: {permalink}")


if __name__ == "__main__":
    main()

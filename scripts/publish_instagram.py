#!/usr/bin/env python3
"""
Refreshes the Instagram long-lived access token, publishes the day's 5-slide
carousel (already pushed to the repo under slides/<date>/, served via
jsDelivr's GitHub CDN), and persists the refreshed token back into this
repo's GitHub Actions secret so tomorrow's run picks it up automatically.

Required env vars:
  IG_ACCESS_TOKEN        current long-lived Instagram token
  IG_USER_ID             Instagram Business/Login user id
  GITHUB_REPOSITORY      owner/repo (set automatically by GitHub Actions)
  SLIDE_DATE             YYYY-MM-DD folder name under slides/
  CONTENT_JSON_PATH      path to today's content.json (default: content.json)

Optional:
  GH_SECRETS_PAT         a PAT with Contents:read + Secrets:read&write on this
                          repo. If unset, the refreshed token is printed but
                          NOT persisted — next run will reuse the old token
                          until someone updates the secret manually.
"""
import base64
import json
import os
import sys
import time

import requests
from nacl import encoding, public

GRAPH = "https://graph.instagram.com/v21.0"


def refresh_token(token):
    r = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def cdn_url(repo, date, i):
    return f"https://cdn.jsdelivr.net/gh/{repo}@main/slides/{date}/slide-{i}.png"


def wait_for_cdn(url, tries=10, delay=6):
    for _ in range(tries):
        try:
            r = requests.head(url, timeout=15, allow_redirects=True)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(delay)
    return False


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


def wait_finished(creation_id, token, tries=8, delay=4):
    for _ in range(tries):
        r = requests.get(
            f"{GRAPH}/{creation_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        r.raise_for_status()
        status = r.json().get("status_code")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            return False
        time.sleep(delay)
    return False


def publish(user_id, token, creation_id):
    r = requests.post(
        f"{GRAPH}/{user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["id"]


def get_permalink(media_id, token):
    r = requests.get(
        f"{GRAPH}/{media_id}", params={"fields": "permalink", "access_token": token}, timeout=30
    )
    r.raise_for_status()
    return r.json().get("permalink")


def build_caption(content):
    lines = [f"🧠 Veille IA du jour — {content['date_fr']}", "", "Ce qu'il faut retenir aujourd'hui :", ""]
    emojis = ["1️⃣", "2️⃣", "3️⃣"]
    for e, item in zip(emojis, content["news"]):
        lines.append(f"{e} {item['headline']}")
    lines += [
        "",
        "Suivez @sanaconsulting.ca pour la veille IA chaque matin ☕️",
        "",
        "#IA #IntelligenceArtificielle #VeilleTechnologique #AI #Innovation #Tech #StartupIA #Consulting",
    ]
    return "\n".join(lines)


def update_secret(repo, pat, name, value):
    headers = {"Authorization": f"Bearer {pat}", "Accept": "application/vnd.github+json"}
    pub = requests.get(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key", headers=headers, timeout=30
    )
    pub.raise_for_status()
    key_data = pub.json()
    public_key = public.PublicKey(key_data["key"].encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(value.encode("utf-8"))
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")
    r = requests.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{name}",
        headers=headers,
        json={"encrypted_value": encrypted_b64, "key_id": key_data["key_id"]},
        timeout=30,
    )
    r.raise_for_status()


def main():
    token = os.environ["IG_ACCESS_TOKEN"]
    user_id = os.environ["IG_USER_ID"]
    repo = os.environ["GITHUB_REPOSITORY"]
    pat = os.environ.get("GH_SECRETS_PAT")
    date = os.environ["SLIDE_DATE"]
    content_path = os.environ.get("CONTENT_JSON_PATH", "content.json")

    with open(content_path, encoding="utf-8") as f:
        content = json.load(f)

    print("Refreshing Instagram token...")
    new_token = refresh_token(token)

    print("Waiting for slides to be reachable via CDN...")
    first_url = cdn_url(repo, date, 1)
    if not wait_for_cdn(first_url):
        print(f"ERROR: {first_url} never became reachable", file=sys.stderr)
        sys.exit(1)

    print("Creating carousel items...")
    children = []
    for i in range(1, 6):
        url = cdn_url(repo, date, i)
        cid = create_carousel_item(user_id, new_token, url)
        children.append(cid)
        print(f"  slide-{i}: {cid}")

    caption = build_caption(content)
    print("Creating carousel container...")
    creation_id = create_carousel_container(user_id, new_token, children, caption)

    print("Waiting for processing...")
    if not wait_finished(creation_id, new_token):
        print("ERROR: carousel did not reach FINISHED status in time", file=sys.stderr)
        sys.exit(1)

    print("Publishing...")
    media_id = publish(user_id, new_token, creation_id)
    permalink = get_permalink(media_id, new_token)
    print(f"Published: {permalink}")

    if pat:
        print("Persisting refreshed token to repo secret IG_ACCESS_TOKEN...")
        update_secret(repo, pat, "IG_ACCESS_TOKEN", new_token)
        print("Done.")
    else:
        print(
            "WARN: GH_SECRETS_PAT not set — refreshed token was NOT persisted. "
            "Next run will reuse the old token until the IG_ACCESS_TOKEN secret "
            "is updated manually or GH_SECRETS_PAT is configured.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()

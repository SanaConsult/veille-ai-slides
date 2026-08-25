"""Shared helpers for publishing to Instagram (carousel + Reels) and for
persisting a refreshed access token back into this repo's GitHub Actions
secrets. Imported by refresh_ig_token.py, publish_carousel.py,
publish_reel.py, and persist_token.py — never run directly.
"""
import base64
import time

import requests

GRAPH = "https://graph.instagram.com/v21.0"


def refresh_token(token):
    r = requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": token},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def cdn_url(repo, date, filename):
    return f"https://cdn.jsdelivr.net/gh/{repo}@main/slides/{date}/{filename}"


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


def wait_finished(creation_id, token, tries=8, delay=5):
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


def publish_container(user_id, token, creation_id):
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
    from nacl import encoding, public

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

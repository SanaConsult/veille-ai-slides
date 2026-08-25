#!/usr/bin/env python3
"""
Builds the 5 HTML slide files for the daily "Veille AI" Instagram carousel,
using the Sana Consulting brand system (navy / gold / white, Playfair Display + Inter).

Usage:
    python3 build_slides.py content.json slides_out_dir

content.json shape:
{
  "date_fr": "24 août 2026",
  "news": [
    {"headline": "...", "summary": "...", "source": "TechCrunch"},
    {"headline": "...", "summary": "...", "source": "..."},
    {"headline": "...", "summary": "...", "source": "..."}
  ],
  "recap": ["short recap 1", "short recap 2", "short recap 3"]
}
"""
import base64
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


LOGO_B64 = b64(os.path.join(ASSETS, "logo.png"))
PLAYFAIR_B64 = b64(os.path.join(ASSETS, "PlayfairDisplay.ttf"))
PLAYFAIR_ITALIC_B64 = b64(os.path.join(ASSETS, "PlayfairDisplayItalic.ttf"))
INTER_B64 = b64(os.path.join(ASSETS, "Inter.ttf"))
NAVY = "#07162D"
NAVY_DEEP = "#050F1F"
GOLD = "#C9A961"
GOLD_SOFT = "#E4C77E"
WHITE = "#FFFFFF"
MUTED = "#9FB0C3"

BASE_CSS = f"""
@font-face {{
  font-family: 'Playfair Display';
  src: url(data:font/ttf;base64,{PLAYFAIR_B64}) format('truetype');
  font-weight: 100 900;
}}
@font-face {{
  font-family: 'Playfair Display';
  font-style: italic;
  src: url(data:font/ttf;base64,{PLAYFAIR_ITALIC_B64}) format('truetype');
  font-weight: 100 900;
}}
@font-face {{
  font-family: 'Inter';
  src: url(data:font/ttf;base64,{INTER_B64}) format('truetype');
  font-weight: 100 900;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{
  width: 1080px; height: 1080px;
  background: linear-gradient(160deg, {NAVY} 0%, {NAVY_DEEP} 100%);
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}}
.canvas {{
  position: relative;
  width: 1080px; height: 1080px;
  padding: 88px 90px;
}}
.bracket {{
  position: absolute;
  width: 46px; height: 64px;
  border-left: 3px solid {GOLD};
  border-top: 3px solid {GOLD};
  border-bottom: 3px solid {GOLD};
  top: 84px; left: 90px;
}}
.eyebrow {{
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 20px;
  letter-spacing: 6px;
  color: {GOLD};
  text-transform: uppercase;
}}
.footer-lockup {{
  position: absolute;
  left: 90px; bottom: 64px;
  display: flex;
  align-items: center;
  gap: 14px;
}}
.footer-lockup .s-badge {{
  width: 34px; height: 34px;
  border: 2px solid {GOLD};
  display: flex; align-items: center; justify-content: center;
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: 20px;
  color: {WHITE};
}}
.footer-lockup .wordmark {{
  font-family: 'Inter', sans-serif;
  font-size: 15px;
  letter-spacing: 3px;
  color: {MUTED};
  text-transform: uppercase;
}}
.footer-lockup .wordmark b {{
  color: {WHITE};
  font-weight: 700;
}}
.dots {{
  position: absolute;
  right: 90px; bottom: 74px;
  display: flex;
  gap: 10px;
}}
.dots span {{
  width: 8px; height: 8px;
  border-radius: 50%;
  background: rgba(159,176,195,0.35);
  display: inline-block;
}}
.dots span.active {{
  background: {GOLD};
  width: 24px;
  border-radius: 4px;
}}
.hairline {{
  width: 64px; height: 3px;
  background: {GOLD};
}}
"""


def page_shell(inner_html, extra_css=""):
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{BASE_CSS}
{extra_css}
</style>
</head>
<body>
<div class="canvas">
{inner_html}
</div>
</body>
</html>"""


def footer_lockup():
    return f"""
<div class="footer-lockup">
  <div class="s-badge">S</div>
  <div class="wordmark"><b>Sana</b> Consulting</div>
</div>
"""


def dots(active_index, total=5):
    spans = "".join(
        f'<span class="{"active" if i == active_index else ""}"></span>'
        for i in range(total)
    )
    return f'<div class="dots">{spans}</div>'


def esc(s):
    return html.escape(s or "")


def slide_title(date_fr):
    extra_css = """
    .title-wrap { position: absolute; left: 90px; top: 360px; width: 780px; }
    .title-wrap h1 { font-family: 'Playfair Display', serif; font-weight: 600; font-size: 104px; line-height: 1.02; color: #FFFFFF; }
    .title-wrap h1 em { font-style: italic; color: #C9A961; }
    .subtitle { margin-top: 26px; font-family: 'Inter', sans-serif; font-size: 24px; color: #9FB0C3; font-weight: 400; letter-spacing: 0.3px; }
    .date-tag { margin-top: 40px; display: inline-block; font-family: 'Inter', sans-serif; font-size: 17px; letter-spacing: 3px; color: #C9A961; text-transform: uppercase; border: 1px solid rgba(201,169,97,0.5); padding: 10px 20px; }
    .logo-full { position: absolute; left: 90px; bottom: 84px; display: flex; align-items: center; gap: 22px; }
    .logo-full img { width: 60px; height: 60px; object-fit: contain; }
    .logo-full .lockup-text { font-family: 'Inter', sans-serif; }
    .logo-full .lockup-text .b1 { font-size: 15px; letter-spacing: 4px; color: #9FB0C3; }
    .swipe { position: absolute; right: 90px; bottom: 90px; font-family:'Inter',sans-serif; font-size:16px; letter-spacing:2px; color:#C9A961; text-transform:uppercase; }
    """
    inner = f"""
<div class="bracket"></div>
<div class="eyebrow">Veille quotidienne</div>
<div class="title-wrap">
  <h1>L'actu <em>IA</em><br>du jour</h1>
  <div class="subtitle">Ce qu'il faut retenir aujourd'hui en intelligence artificielle</div>
  <div class="date-tag">{esc(date_fr)}</div>
</div>
{footer_lockup()}
<div class="swipe">Swipe →</div>
"""
    return page_shell(inner, extra_css)


def slide_news(item, idx, total):
    headline = item.get("headline", "")
    summary = item.get("summary", "")
    source = item.get("source", "")
    # scale headline font size down a bit if long
    size = 64
    if len(headline) > 70:
        size = 54
    if len(headline) > 100:
        size = 46
    extra_css = f"""
    .num {{ position: absolute; left: 90px; top: 210px; font-family:'Playfair Display',serif; font-size: 130px; color: rgba(201,169,97,0.18); font-weight:700; line-height:1; }}
    .news-wrap {{ position: absolute; left: 90px; top: 300px; width: 860px; }}
    .headline {{ font-family: 'Playfair Display', serif; font-weight: 600; font-size: {size}px; line-height: 1.12; color: #FFFFFF; }}
    .hairline-wrap {{ margin: 30px 0; }}
    .summary {{ font-family: 'Inter', sans-serif; font-size: 25px; line-height: 1.55; color: #C7D2E0; font-weight: 400; max-width: 820px; }}
    .source {{ position: absolute; left: 90px; bottom: 130px; font-family:'Inter',sans-serif; font-size: 16px; letter-spacing: 2px; color:#C9A961; text-transform:uppercase; }}
    """
    inner = f"""
<div class="bracket"></div>
<div class="eyebrow">Actualité {idx} / {total}</div>
<div class="num">0{idx}</div>
<div class="news-wrap">
  <div class="headline">{esc(headline)}</div>
  <div class="hairline-wrap"><div class="hairline"></div></div>
  <div class="summary">{esc(summary)}</div>
</div>
<div class="source">Source · {esc(source)}</div>
{footer_lockup()}
{dots(idx)}
"""
    return page_shell(inner, extra_css)


def slide_cta(recap):
    items_html = ""
    for i, line in enumerate(recap[:3], start=1):
        items_html += f"""
<div class="recap-item">
  <div class="recap-num">0{i}</div>
  <div class="recap-text">{esc(line)}</div>
</div>"""
    extra_css = """
    .cta-title { position: absolute; left: 90px; top: 210px; font-family:'Playfair Display',serif; font-weight:600; font-size: 62px; color:#FFFFFF; width: 780px; line-height:1.08; }
    .recap-list { position: absolute; left: 90px; top: 380px; width: 860px; display: flex; flex-direction: column; gap: 26px; }
    .recap-item { display: flex; gap: 22px; align-items: flex-start; }
    .recap-num { font-family:'Inter',sans-serif; font-size: 16px; color:#C9A961; font-weight:700; letter-spacing:1px; padding-top: 4px; }
    .recap-text { font-family:'Inter',sans-serif; font-size: 22px; color:#C7D2E0; line-height:1.4; max-width: 760px; }
    .cta-box { position: absolute; left: 90px; bottom: 210px; }
    .cta-box .handle { font-family:'Playfair Display',serif; font-style:italic; font-size: 42px; color:#FFFFFF; }
    .cta-box .handle b { color:#C9A961; font-style: normal; }
    .cta-box .sub { margin-top:12px; font-family:'Inter',sans-serif; font-size:19px; color:#9FB0C3; letter-spacing:0.5px; }
    """
    inner = f"""
<div class="bracket"></div>
<div class="eyebrow">En bref</div>
<div class="cta-title">Ce qu'il faut<br>retenir aujourd'hui</div>
<div class="recap-list">{items_html}</div>
<div class="cta-box">
  <div class="handle">Suivez <b>@sanaconsulting.ca</b></div>
  <div class="sub">Pour la veille IA, chaque matin.</div>
</div>
{footer_lockup()}
{dots(4)}
"""
    return page_shell(inner, extra_css)


def main():
    if len(sys.argv) < 3:
        print("Usage: build_slides.py content.json out_dir")
        sys.exit(1)
    content_path, out_dir = sys.argv[1], sys.argv[2]
    with open(content_path, "r", encoding="utf-8") as f:
        content = json.load(f)
    os.makedirs(out_dir, exist_ok=True)

    files = []

    p = os.path.join(out_dir, "slide-1.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(slide_title(content["date_fr"]))
    files.append(p)

    news = content["news"]
    for i, item in enumerate(news, start=1):
        p = os.path.join(out_dir, f"slide-{i+1}.html")
        with open(p, "w", encoding="utf-8") as f:
            f.write(slide_news(item, i, len(news)))
        files.append(p)

    p = os.path.join(out_dir, f"slide-{len(news)+2}.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(slide_cta(content.get("recap", [n["headline"] for n in news])))
    files.append(p)

    print("Wrote:", *files, sep="\n  ")


if __name__ == "__main__":
    main()

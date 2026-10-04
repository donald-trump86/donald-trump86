"""Run with python3 tests/check_profile.py; no third-party dependencies."""
from html.parser import HTMLParser
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"svg": "http://www.w3.org/2000/svg"}


class ProfileHTML(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img":
            assert attrs.get("alt"), f"Missing alternative text: {attrs}"
        for attr in ("src", "srcset"):
            value = attrs.get(attr, "")
            if value and not value.startswith("https://"):
                assert (ROOT / value).is_file(), f"Missing local asset: {value}"
        if attrs.get("src") == "assets/avatar.png":
            assert attrs.get("align") == "left", "Avatar must remain on the left"
            assert attrs.get("width") == attrs.get("height") == "136"


readme = (ROOT / "README.md").read_text()
ProfileHTML().feed(readme)
assert "<br clear=\"left\">" in readme, "Clear avatar before project section"
assert "ghchart.rshah.org/22b8a8/donald-trump86" in readme
assert "activity-graph.herokuapp.com" not in readme
for name in ("dsh-bar-macos", "xiaoxi-dormsense", "Quick-ZSH", "Selfuse-IPA-Source"):
    assert f"github.com/donald-trump86/{name}" in readme
for content in ("MacBook Air（M5）", "iPad Pro（2024）", "Minecraft", "Call of Duty"):
    assert content in readme
assert '(prefers-color-scheme: dark)' in readme

assert readme.index('srcset="assets/profile-dark-mobile.svg"') < readme.index('srcset="assets/profile-light-mobile.svg"') < readme.index('srcset="assets/profile-dark.svg"')
for theme in ("dark", "light", "dark-mobile", "light-mobile"):
    svg = ET.parse(ROOT / f"assets/profile-{theme}.svg").getroot()
    mobile = theme.endswith("mobile")
    assert svg.attrib["viewBox"] == ("0 0 640 260" if mobile else "0 0 1200 400")
    assert svg.attrib["aria-labelledby"] == "title desc"
    assert svg.find("svg:title", NS) is not None
    assert svg.find("svg:desc", NS) is not None
    css = svg.find("svg:defs/svg:style", NS).text
    assert "prefers-reduced-motion:reduce" in css
    assert "animation:none" in css
    assert "@keyframes typing" in css
    if not mobile:
        assert "@keyframes orbit" in css
    assert "@keyframes caret" in css and "steps(32,end)" in css
    clip = svg.find("svg:defs/svg:clipPath[@id='typed']/svg:rect", NS)
    typed = svg.find(".//svg:text[@clip-path='url(#typed)']", NS)
    assert clip.attrib["width"] == typed.attrib["textLength"] == "404"
    assert len(typed.text) == 32, "Typing steps must match the text length"
    assert not svg.findall(".//svg:script", NS)
    assert not svg.findall(".//svg:foreignObject", NS)
    assert not svg.findall(".//svg:image", NS), "Header must render without external assets"
    ids = {node.attrib["id"] for node in svg.iter() if "id" in node.attrib}
    for node in svg.iter():
        for value in node.attrib.values():
            if value.startswith("url(#"):
                assert value[5:-1] in ids, f"Broken SVG reference: {value}"

png = (ROOT / "assets/avatar.png").read_bytes()
assert png[:8] == b"\x89PNG\r\n\x1a\n"
assert struct.unpack(">II", png[16:24]) == (400, 400)
print("PASS: both headers, motion fallback, left avatar, local assets, alt text and preserved profile content")

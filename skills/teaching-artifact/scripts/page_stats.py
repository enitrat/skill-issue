#!/usr/bin/env python3
"""Text-budget and highlight check for a teaching artifact.

Usage: python3 -I page_stats.py page.html

Prints:
- visible prose words (outside <details>, <pre>, <table>, <svg>, <script>, <style>, <code>)
- per <section>: its heading, visible words, and any paragraph/caption/list item over 3 sentences
- every <pre class="code"> block's header label and its highlighted lines, so off-by-one
  data-hl values are caught before publishing.
Exit code 1 when visible words >= 900 or any prose block has more than 3 sentences.
"""
import html
import re
import sys
from html.parser import HTMLParser

SKIP = {"details", "pre", "table", "svg", "script", "style", "code", "title"}
WORD_LIMIT = 900
SENTENCE_LIMIT = 3
BLOCKS = {"p", "li", "figcaption", "dd"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.stack = []
        self.sections = []  # [heading, text]
        self.words = []
        self.blocks = []  # (hl, text)
        self.in_pre = None
        self.in_heading = False
        self.block = None  # text of the open prose block

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "section":
            self.sections.append(["(untitled)", ""])
        if tag in ("h1", "h2") and self.sections and self.skip_depth == 0:
            self.in_heading = True
            self.sections[-1][0] = ""
        if tag == "pre" and "code" in (a.get("class") or "").split():
            self.in_pre = [a.get("data-hl") or "", ""]
        if tag in BLOCKS and self.skip_depth == 0 and self.block is None:
            self.block = [tag, ""]
        if tag in SKIP:
            self.skip_depth += 1
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in ("h1", "h2"):
            self.in_heading = False
        if tag == "pre" and self.in_pre is not None:
            self.blocks.append(tuple(self.in_pre))
            self.in_pre = None
        if tag in SKIP and self.skip_depth:
            self.skip_depth -= 1
        if self.block is not None and tag == self.block[0]:
            if self.sections:
                self.sections[-1].append(self.block[1])
            self.block = None

    def handle_data(self, data):
        if self.in_pre is not None:
            self.in_pre[1] += data
            return
        if self.skip_depth:
            return
        if self.in_heading and self.sections:
            self.sections[-1][0] += data
            return
        text = data.strip()
        if not text:
            return
        self.words.extend(text.split())
        if self.sections:
            self.sections[-1][1] += " " + text
        if self.block is not None:
            self.block[1] += " " + text


def lines_of(spec):
    out = set()
    for part in filter(None, spec.split(",")):
        lo, _, hi = part.partition("-")
        out.update(range(int(lo), int(hi or lo) + 1))
    return sorted(out)


def main(path):
    page = Page()
    page.feed(open(path, encoding="utf-8").read())
    failed = False
    n = len(page.words)
    print(f"visible prose words: {n} (limit < {WORD_LIMIT})")
    failed |= n >= WORD_LIMIT
    print("\nsections (visible words):")
    for heading, text, *blocks in page.sections:
        print(f"  {len(text.split()):4d}  {heading.strip()[:70]}")
        for block in blocks:
            count = len([x for x in re.split(r"(?<=[.!?])\s+", block.strip()) if len(x.split()) > 2])
            if count > SENTENCE_LIMIT:
                failed = True
                print(f"        over: {count} sentences: {block.strip()[:90]}...")
    print("\nhighlighted lines per code block:")
    for i, (hl, code) in enumerate(page.blocks, 1):
        if not hl:
            continue
        lines = html.unescape(code).rstrip("\n").split("\n")
        print(f"  block {i} (data-hl={hl}, {len(lines)} lines)")
        for ln in lines_of(hl):
            if ln > len(lines):
                failed = True
            body = lines[ln - 1] if ln <= len(lines) else "<<OUT OF RANGE>>"
            print(f"    {ln:3d} | {body}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

from __future__ import annotations

import logging
import re
from typing import Any

from lxml import etree, html
from lxml.etree import _Element

logger = logging.getLogger(__name__)


def normalize_html(html_str: str) -> str:
    try:
        parser = etree.HTMLParser()
        tree = etree.fromstring(html_str.encode('utf-8'), parser)

        for script in tree.xpath("//script"):
            script.getparent().remove(script)

        for comment in tree.xpath("//comment()"):
            comment.getparent().remove(comment)

        for el in tree.xpath("//*[@class]"):
            del el.attrib["class"]

        for el in tree.xpath("//*"):
            keys_to_remove = [k for k in el.attrib if k.startswith('data-') or k.startswith('on')]
            for key in keys_to_remove:
                del el.attrib[key]

        for el in tree.xpath("//*[@src]"):
            if el.attrib["src"].startswith("data:"):
                el.attrib["src"] = "data:normalized"

        for el in tree.xpath("//*[@style]"):
            del el.attrib["style"]

        browser_attrs = {'image_error', 'image_loaded', 'ans_ss_dlg'}
        for el in tree.xpath("//*"):
            for attr in browser_attrs & set(el.attrib):
                del el.attrib[attr]

        _uuid_re = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
        for el in tree.xpath("//*"):
            keys_to_remove = [k for k in el.attrib if '.' in k or _uuid_re.match(k)]
            for key in keys_to_remove:
                del el.attrib[key]

        for el in tree.xpath("//img | //video | //source | //audio"):
            el.getparent().remove(el)
        for el in tree.xpath("//a"):
            el.attrib.pop("href", None)

        for tbody in tree.xpath("//tbody"):
            parent = tbody.getparent()
            idx = list(parent).index(tbody)
            for i, child in enumerate(tbody):
                parent.insert(idx + i, child)
            parent.remove(tbody)

        result = etree.tostring(tree, encoding='unicode', method='html')

        bool_attrs = ('hidden', 'disabled', 'checked', 'readonly', 'required',
                      'autofocus', 'autoplay', 'controls', 'loop', 'muted',
                      'novalidate', 'open', 'selected', 'multiple')
        for attr in bool_attrs:
            result = re.sub(rf'\b{attr}=""', attr, result)
        return ' '.join(result.split())

    except Exception as e:
        logger.error("Error normalizing HTML: %s", e)
        return html_str


def parse_with_xpath(
    html_content: str,
    xpath: str,
    extract: bool = False,
    highlight: bool = True,
    label: str | None = None,
) -> dict[str, list[str] | None]:
    result: dict[str, list[str] | None] = {
        "extracted_elements": [],
        "highlighted_html": None
    }

    if not extract and not highlight:
        logger.warning("parse_with_xpath called with both flags False")
        return result

    try:
        tree = html.fromstring(html_content)
        elements = tree.xpath(xpath)

        if not elements:
            return result

        if highlight:
            marker_text = label if label else f'Match {len(elements)}'
            for elem in elements:
                elem.set('style', '''
                    border: 4px solid #ff5722 !important;
                    background: #fff3e0 !important;
                    padding: 10px !important;
                    margin: 10px !important;
                    display: block !important;
                    visibility: visible !important;
                ''')

                marker = html.Element('div')
                marker.set('style', '''
                    background: #ff5722 !important;
                    color: white !important;
                    padding: 4px 10px !important;
                    margin: 0 0 5px 0 !important;
                    font-size: 12px !important;
                    font-weight: bold !important;
                ''')
                marker.text = marker_text
                elem.insert(0, marker)

            result["highlighted_html"] = html.tostring(
                tree,
                encoding='unicode',
                method='html',
                doctype='<!DOCTYPE html>'
            )

        if extract:
            result["extracted_elements"] = [
                html.tostring(elem, encoding='unicode', method='html')
                for elem in elements
            ]

        return result

    except Exception as e:
        logger.error("Error parsing HTML with XPath '%s': %s", xpath, e)
        return result


def resolve_html_content(scrb: Any) -> str | None:
    html_content = getattr(scrb, "html_content", None)
    if isinstance(html_content, str) and html_content.strip():
        return html_content

    stream = getattr(scrb, "html_stream", None)
    if stream is None:
        return None

    try:
        if hasattr(stream, "read"):
            raw = stream.read()
        else:
            raw = stream

        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
        if isinstance(raw, str):
            return raw
    except Exception:
        return None

    return None


def evaluate_xpath_nodes(html_content: str, xpath_expr: str | None) -> list[_Element]:
    if not html_content or not xpath_expr:
        return []

    try:
        tree = html.fromstring(html_content)
    except Exception:
        return []

    try:
        nodes = tree.xpath(xpath_expr)
    except Exception:
        return []

    return [n for n in nodes if isinstance(n, _Element)]


def select_first(node: _Element, candidates: list[str]) -> _Element | None:
    for xp in candidates:
        try:
            out = node.xpath(xp)
        except Exception:
            continue
        for item in out:
            if isinstance(item, _Element):
                return item
    return None


def select_all(node: _Element, candidates: list[str]) -> list[_Element]:
    results: list[_Element] = []
    seen: set[int] = set()
    for xp in candidates:
        try:
            out = node.xpath(xp)
        except Exception:
            continue
        for item in out:
            if not isinstance(item, _Element):
                continue
            key = id(item)
            if key in seen:
                continue
            seen.add(key)
            results.append(item)
    return results

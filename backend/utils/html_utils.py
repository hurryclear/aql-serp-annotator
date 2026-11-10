import logging
import re

import lxml.html
from lxml import etree

from exceptions import InvalidMarkError

logger = logging.getLogger(__name__)


# our own attributes in a snapshot, prefixed with the project name so they never
# clash with the SERP's own attributes
NODE_ATTR = "aqlqa-node"     # every element's number, written once when the snapshot is cached
TYPE_ATTR = "aqlqa-sf-type"  # on a marked element: its feature type
# No feature id in the page: the n-th element (in page order) with
# aqlqa-sf-type="T" is the Feature row with feature_type T and id
# uuid5(serp_id:T:n), so the id can always be recomputed from the page.


def _parse(html_str: str) -> etree._Element:
    # bytes + explicit encoding: lxml refuses str input that carries an
    # <?xml encoding=...?> declaration, which some archived pages have
    parser = lxml.html.HTMLParser(encoding="utf-8")
    return lxml.html.document_fromstring(html_str.encode("utf-8"), parser=parser)


def _serialize(root: etree._Element) -> str:
    return etree.tostring(root.getroottree(), method="html", encoding="unicode")


def number_elements(html_str: str) -> str:
    """Give every element a unique aqlqa-node number, 1, 2, 3, ... in document order.

    The numbers are stored in the snapshot, so the browser can read the number off
    the element the annotator marked and the backend finds the very same element
    later, even where the browser's DOM differs from lxml's (e.g. added <tbody>).
    """
    root = _parse(html_str)
    for number, element in enumerate(root.iter(etree.Element), start=1):
        element.set(NODE_ATTR, str(number))
    return _serialize(root)


def marked_nodes(html_str: str) -> list[tuple[int, str]]:
    """(node number, feature type) of every marked element, in page order."""
    root = _parse(html_str)
    return [
        (int(element.get(NODE_ATTR)), element.get(TYPE_ATTR))
        for element in root.iter(etree.Element)
        if element.get(TYPE_ATTR) is not None and element.get(NODE_ATTR) is not None
    ]


def mark_features(html_str: str, marks: list[tuple[int, str]], clear_old: bool = False) -> str:
    """Write aqlqa-sf-type onto the elements with these numbers.

    marks: (node number, feature type) per feature. clear_old removes every
    existing aqlqa-sf-type first, as when an edited annotation replaces the old
    one. Raises InvalidMarkError if a number isn't in the snapshot.
    """
    root = _parse(html_str)
    if clear_old:
        for element in root.iter(etree.Element):
            element.attrib.pop(TYPE_ATTR, None)
    by_number = {element.get(NODE_ATTR): element for element in root.iter(etree.Element)}
    for node, feature_type in marks:
        element = by_number.get(str(node))
        if element is None:
            raise InvalidMarkError(f"element {node} is not in this SERP's snapshot")
        element.set(TYPE_ATTR, feature_type)
    return _serialize(root)


_POPUP_HIDER_CSS = """
<style id="annotation-popup-hider">
    div[role="dialog"], div[role="alertdialog"],
    div[class*="popup"], div[class*="modal"], div[class*="overlay"],
    div[class*="consent"], div[class*="cookie"], div[class*="gdpr"],
    div[id*="popup"], div[id*="modal"], div[id*="overlay"],
    div[class*="spinner"], div[class*="loader"] {
        display: none !important;
    }
    body, html {
        display: block !important;
        overflow: auto !important;
        position: static !important;
    }
</style>
"""


def _inject_into_head(html_str: str, snippet: str) -> str:
    # put the snippet right after <head>, else after <html>, else at the very top
    for tag_pattern in (r"(<head[^>]*>)", r"(<html[^>]*>)"):
        if re.search(tag_pattern, html_str, re.IGNORECASE):
            return re.sub(
                tag_pattern,
                lambda m: m.group(1) + snippet,
                html_str,
                count=1,
                flags=re.IGNORECASE,
            )
    return snippet + html_str


def clean_serp_html(html_str: str, base_url: str | None = None) -> str:
    """Make an archived SERP safe and static for annotation: strip scripts,
    redirects and inline event handlers, point relative links at the
    original domain, and hide cookie banners/popups."""
    html_str = re.sub(
        r'<meta[^>]*http-equiv=["\']?refresh["\']?[^>]*>',
        "<!-- meta refresh removed -->",
        html_str,
        flags=re.IGNORECASE,
    )
    html_str = re.sub(
        r"<script[^>]*>.*?</script>",
        "<!-- script removed for annotation -->",
        html_str,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html_str = re.sub(
        r'\s+on\w+\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)',
        "",
        html_str,
        flags=re.IGNORECASE,
    )
    html_str = re.sub(
        r"<noscript[^>]*>.*?</noscript>",
        "<!-- noscript removed -->",
        html_str,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if base_url:
        match = re.match(r"(https?://[^/]+)/", base_url)
        if match:
            base_tag = f'<base href="{match.group(1)}/" target="_self">\n'
            html_str = _inject_into_head(html_str, base_tag)

    return _inject_into_head(html_str, _POPUP_HIDER_CSS)


_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_BROWSER_ATTRS = {"image_error", "image_loaded", "ans_ss_dlg"}
_BOOL_ATTRS = (
    "hidden",
    "disabled",
    "checked",
    "readonly",
    "required",
    "autofocus",
    "autoplay",
    "controls",
    "loop",
    "muted",
    "novalidate",
    "open",
    "selected",
    "multiple",
)


def normalize_html(html_str: str) -> str:
    """Reduce an HTML fragment to a comparable form, dropping everything a
    browser or our own highlighting may have changed (classes, styles,
    data-* attributes, media, hrefs, <tbody> wrappers, whitespace)."""
    try:
        tree = etree.fromstring(html_str.encode("utf-8"), etree.HTMLParser())

        for node in tree.xpath("//script | //comment()"):
            node.getparent().remove(node)

        for el in tree.xpath("//*"):
            for key in list(el.attrib):
                if (
                    key in ("class", "style")
                    or key.startswith(("data-", "on"))
                    or key in _BROWSER_ATTRS
                    or "." in key
                    or _UUID_RE.match(key)
                ):
                    del el.attrib[key]

        for el in tree.xpath("//*[@src]"):
            if el.attrib["src"].startswith("data:"):
                el.attrib["src"] = "data:normalized"

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

        result = etree.tostring(tree, encoding="unicode", method="html")
        for attr in _BOOL_ATTRS:
            result = re.sub(rf'\b{attr}=""', attr, result)
        return " ".join(result.split())

    except Exception as e:
        logger.error("Error normalizing HTML: %s", e)
        return html_str

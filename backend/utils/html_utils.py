"""HTML helpers ported from the old Flask tool.

clean_serp_html: src/annotation/utils/html_cleaning.py
normalize_html:  src/parser/utils/html_utils.py
"""
import logging
import re

from lxml import etree

logger = logging.getLogger(__name__)


_POPUP_HIDER_CSS = '''
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
'''


def _inject_into_head(html_str: str, snippet: str) -> str:
    # put the snippet right after <head>, else after <html>, else at the very top
    for tag_pattern in (r'(<head[^>]*>)', r'(<html[^>]*>)'):
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
        '<!-- meta refresh removed -->',
        html_str,
        flags=re.IGNORECASE,
    )
    html_str = re.sub(
        r'<script[^>]*>.*?</script>',
        '<!-- script removed for annotation -->',
        html_str,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html_str = re.sub(
        r'\s+on\w+\s*=\s*["\'][^"\']*["\']',
        '',
        html_str,
        flags=re.IGNORECASE,
    )
    html_str = re.sub(
        r'<noscript[^>]*>.*?</noscript>',
        '<!-- noscript removed -->',
        html_str,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if base_url:
        match = re.match(r'(https?://[^/]+)/', base_url)
        if match:
            base_tag = f'<base href="{match.group(1)}/" target="_self">\n'
            html_str = _inject_into_head(html_str, base_tag)

    return _inject_into_head(html_str, _POPUP_HIDER_CSS)


_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
_BROWSER_ATTRS = {'image_error', 'image_loaded', 'ans_ss_dlg'}
_BOOL_ATTRS = ('hidden', 'disabled', 'checked', 'readonly', 'required',
               'autofocus', 'autoplay', 'controls', 'loop', 'muted',
               'novalidate', 'open', 'selected', 'multiple')


def normalize_html(html_str: str) -> str:
    """Reduce an HTML fragment to a comparable form, dropping everything a
    browser or our own highlighting may have changed (classes, styles,
    data-* attributes, media, hrefs, <tbody> wrappers, whitespace)."""
    try:
        tree = etree.fromstring(html_str.encode('utf-8'), etree.HTMLParser())

        for node in tree.xpath("//script | //comment()"):
            node.getparent().remove(node)

        for el in tree.xpath("//*"):
            for key in list(el.attrib):
                if (
                    key in ('class', 'style')
                    or key.startswith(('data-', 'on'))
                    or key in _BROWSER_ATTRS
                    or '.' in key
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

        result = etree.tostring(tree, encoding='unicode', method='html')
        for attr in _BOOL_ATTRS:
            result = re.sub(rf'\b{attr}=""', attr, result)
        return ' '.join(result.split())

    except Exception as e:
        logger.error("Error normalizing HTML: %s", e)
        return html_str
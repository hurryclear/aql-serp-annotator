from __future__ import annotations

import re


def clean_serp_html(html_bytes: bytes, base_url: str | None = None) -> bytes:
    html_str = html_bytes.decode('utf-8', errors='ignore')

    html_str = re.sub(
        r'<meta[^>]*http-equiv=["\']?refresh["\']?[^>]*>',
        '<!-- meta refresh removed -->',
        html_str,
        flags=re.IGNORECASE
    )

    html_str = re.sub(
        r'<script[^>]*>.*?</script>',
        '<!-- script removed for annotation -->',
        html_str,
        flags=re.IGNORECASE | re.DOTALL
    )

    html_str = re.sub(
        r'\s+on\w+\s*=\s*["\'][^"\']*["\']',
        '',
        html_str,
        flags=re.IGNORECASE
    )

    html_str = re.sub(
        r'<noscript[^>]*>.*?</noscript>',
        '<!-- noscript removed -->',
        html_str,
        flags=re.IGNORECASE | re.DOTALL
    )

    if base_url:
        match = re.match(r'(https?://[^/]+)/', base_url)
        if match:
            base_domain = match.group(1) + '/'
            base_tag = f'<base href="{base_domain}" target="_self">\n'

            injected = False
            if re.search(r'<head[^>]*>', html_str, re.IGNORECASE):
                html_str = re.sub(
                    r'(<head[^>]*>)',
                    r'\1' + base_tag,
                    html_str,
                    count=1,
                    flags=re.IGNORECASE
                )
                injected = True
            elif re.search(r'<html[^>]*>', html_str, re.IGNORECASE):
                html_str = re.sub(
                    r'(<html[^>]*>)',
                    r'\1' + base_tag,
                    html_str,
                    count=1,
                    flags=re.IGNORECASE
                )
                injected = True

            if not injected:
                html_str = base_tag + html_str

    popup_hider_css = '''
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

    if '<head' in html_str.lower():
        html_str = re.sub(
            r'(<head[^>]*>)',
            r'\1' + popup_hider_css,
            html_str,
            count=1,
            flags=re.IGNORECASE
        )
    elif '<html' in html_str.lower():
        html_str = re.sub(
            r'(<html[^>]*>)',
            r'\1' + popup_hider_css,
            html_str,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        html_str = popup_hider_css + html_str

    return html_str.encode('utf-8')

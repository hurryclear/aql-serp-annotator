import re

import pytest

from exceptions import InvalidMarkError
from utils.html_utils import clean_serp_html, mark_features, number_elements


def test_strips_handler_whose_value_contains_the_other_quote():
    # the value holds single quotes inside double quotes; stopping at the first '
    # would leave `query=',true)"` behind and break the tag
    html = """<a href="/x" onclick="navBar(this,'query=',true)">Next</a><p>after</p>"""
    assert clean_serp_html(html).endswith("""<a href="/x">Next</a><p>after</p>""")


def test_strips_unquoted_handler():
    assert "onload" not in clean_serp_html("<body onload=init()><p>x</p></body>")


def test_number_elements_numbers_every_element_in_document_order():
    html = number_elements("<html><body><div><p>a</p></div><!-- c --><span>b</span></body></html>")
    tags = re.findall(r'<(\w+) aqlqa-node="(\d+)"', html)
    assert tags == [("html", "1"), ("body", "2"), ("div", "3"), ("p", "4"), ("span", "5")]
    assert "<!-- c -->" in html  # comments stay, but get no number


def test_mark_features_marks_only_the_numbered_elements():
    numbered = number_elements("<html><body><div>a</div><div>b</div></body></html>")
    marked = mark_features(numbered, [(4, "knowledge_panel")])
    assert '<div aqlqa-node="3">a</div>' in marked
    assert '<div aqlqa-node="4" aqlqa-sf-type="knowledge_panel">b</div>' in marked


def test_mark_features_refuses_an_unknown_number():
    numbered = number_elements("<html><body><div>a</div></body></html>")
    with pytest.raises(InvalidMarkError):
        mark_features(numbered, [(99, "knowledge_panel")])

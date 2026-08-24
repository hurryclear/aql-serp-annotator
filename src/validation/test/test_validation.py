from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4, uuid5, NAMESPACE_DNS

from docs.adr.src.parser.models import Answer, FeatureBlock
from docs.adr.src.validation.validation import (
    validate_xpath_syntax,
    extract_by_xpath,
    count_xpath_matches,
    compare_with_ground_truth,
)


def _serp_uuid(label: str) -> UUID:
    return uuid5(NAMESPACE_DNS, label)


class TestReExportedFunctions:
    def test_validate_xpath_syntax_valid(self):
        result = validate_xpath_syntax("//div[@class='test']")
        assert result["valid"] is True

    def test_validate_xpath_syntax_invalid(self):
        result = validate_xpath_syntax("//div[")
        assert result["valid"] is False

    def test_extract_by_xpath(self):
        html = "<html><body><div class='a'>hello</div><div class='b'>world</div></body></html>"
        results = extract_by_xpath(html, "//div[@class='a']")
        assert len(results) == 1
        assert "hello" in results[0]

    def test_count_xpath_matches(self):
        html = "<html><body><p>one</p><p>two</p><p>three</p></body></html>"
        assert count_xpath_matches(html, "//p") == 3


class TestCompareWithGroundTruth:
    def _make_gt_dir(self, tmp: Path, serp_uuid: UUID, gt_html: str) -> Path:
        gt_dir = tmp / "gt"
        gt_dir.mkdir(parents=True, exist_ok=True)
        (gt_dir / f"{serp_uuid}.html").write_text(gt_html, encoding="utf-8")
        return gt_dir

    def _make_fb(self, serp_id: UUID, category: str, content: str = "", xpath: str | None = None) -> FeatureBlock:
        return FeatureBlock(
            id=uuid4(),
            serp_id=serp_id,
            category=category,
            provider_id=uuid4(),
            year=2024,
            rank=0,
            content=content,
            parser_id=uuid4(),
            xpath=xpath,
        )

    def test_matched(self, tmp_path):
        gt_html = '<html><body><div class="fb" data-fb-category="featured_snippet"><p>Answer</p></div></body></html>'
        sid = _serp_uuid("serp-001")
        gt_dir = self._make_gt_dir(tmp_path, sid, gt_html)

        from lxml import html as lxml_html
        tree = lxml_html.fromstring(gt_html)
        el = tree.xpath("//*[contains(@class, 'fb')]")[0]
        el_html = lxml_html.tostring(el, encoding="unicode", method="html")

        fb = self._make_fb(sid, "featured_snippet", content=el_html)
        result = compare_with_ground_truth([fb], gt_dir)
        assert result["summary"]["matched"] == 1

    def test_no_ground_truth(self, tmp_path):
        gt_dir = tmp_path / "gt" / "annotated_serp"
        gt_dir.mkdir(parents=True)

        sid = _serp_uuid("serp-999")
        fb = self._make_fb(sid, "featured_snippet", content="<div>test</div>")
        result = compare_with_ground_truth([fb], tmp_path / "gt")
        assert result["summary"]["no_ground_truth"] == 1

    def test_missing_gt_element(self, tmp_path):
        gt_html = '<html><body><div class="fb" data-fb-category="knowledge_panel"><p>KP</p></div></body></html>'
        sid = _serp_uuid("serp-002")
        gt_dir = self._make_gt_dir(tmp_path, sid, gt_html)

        fb = self._make_fb(sid, "featured_snippet", content="<div>something else</div>")
        result = compare_with_ground_truth([fb], gt_dir)
        assert result["summary"].get("missing", 0) == 1
        assert result["summary"].get("extra", 0) == 1

    def test_extraction_failed(self, tmp_path):
        gt_html = '<html><body><div class="fb" data-fb-category="featured_snippet"><p>Answer</p></div></body></html>'
        sid = _serp_uuid("serp-003")
        gt_dir = self._make_gt_dir(tmp_path, sid, gt_html)

        fb = self._make_fb(sid, "featured_snippet", content="")
        result = compare_with_ground_truth([fb], gt_dir)
        assert result["summary"]["extraction_failed"] == 1

    def test_result_uses_feature_id_key(self, tmp_path):
        gt_dir = tmp_path / "gt" / "annotated_serp"
        gt_dir.mkdir(parents=True)

        sid = _serp_uuid("serp-010")
        fb = self._make_fb(sid, "featured_snippet", content="<div>test</div>")
        result = compare_with_ground_truth([fb], tmp_path / "gt")
        assert "feature_id" in result["results"][0]
        assert "scrb_id" not in result["results"][0]


class TestFeatureBlockRoundTrip:
    def test_to_dict_from_dict(self):
        fb = FeatureBlock(
            id=uuid4(), serp_id=uuid4(), category="featured_snippet",
            provider_id=uuid4(), year=2024, rank=0, content="<div>test</div>",
            parser_id=uuid4(),
            answers=[
                Answer(text="Paris", source="https://example.com"),
                Answer(text="Capital of France"),
            ],
        )
        d = fb.to_dict()
        restored = FeatureBlock.from_dict(d)
        assert restored.category == fb.category
        assert restored.id == fb.id
        assert restored.serp_id == fb.serp_id
        assert len(restored.answers) == 2
        assert restored.answers[0].text == "Paris"
        assert restored.answers[0].source == "https://example.com"
        assert restored.answers[1].text == "Capital of France"
        assert restored.answers[1].source == ""
        assert restored.content == fb.content

    def test_to_dict_omits_empty_answers(self):
        fb = FeatureBlock(
            id=uuid4(), serp_id=uuid4(), category="paa",
            provider_id=uuid4(), year=2023, rank=1, content="<div/>",
            parser_id=uuid4(),
        )
        d = fb.to_dict()
        assert "answers" not in d

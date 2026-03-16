import json
import re
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from agent.scorer import _parse_json, score_articles


def _make_article(**overrides):
    base = {
        "title": "Test headline",
        "url": "https://example.com/article",
        "summary": "A short summary of the article.",
        "published": datetime(2026, 3, 16, 10, 0, tzinfo=timezone.utc),
        "category": "Tech",
        "source_name": "SVT Nyheter",
    }
    base.update(overrides)
    return base


def _extract_prompt_articles(prompt_text: str) -> list[dict]:
    """Extract the articles JSON array from a scorer prompt."""
    match = re.search(r"return your top \d+:\n\n(.+?)\n\nReturn this exact", prompt_text, re.DOTALL)
    return json.loads(match.group(1))


def _fake_claude_response(id_map: dict):
    """Build a valid Claude JSON response using the short IDs that were generated."""
    ids = list(id_map.keys())
    selected = []
    for sid in ids[:5]:
        selected.append({
            "article_id": sid,
            "representative_source": "SVT Nyheter",
            "cluster_sources": ["SVT Nyheter"],
            "scores": {
                "corroboration": 10,
                "recency": 20,
                "impact": 15,
                "novelty": 8,
                "authority": 7,
            },
            "total": 60,
            "reasoning": "Important story.",
        })
    return json.dumps({
        "selected": selected,
        "rejected_count": max(0, len(ids) - 5),
        "scoring_notes": "",
    })


def _mock_create_fn(captured: list):
    """Return a fake_create function that captures prompt articles."""
    def fake_create(**kwargs):
        prompt_text = kwargs["messages"][0]["content"]
        prompt_articles = _extract_prompt_articles(prompt_text)
        captured.extend(prompt_articles)
        id_map = {a["id"]: a for a in prompt_articles}

        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text=_fake_claude_response(id_map))]
        mock_resp.stop_reason = "end_turn"
        return mock_resp
    return fake_create


class TestPromptConstruction:
    """Verify that article fields are correctly mapped for the scoring prompt."""

    def test_source_name_mapped_to_source(self):
        """source_name in article dict becomes 'source' in the prompt."""
        captured = []
        with patch("agent.scorer.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create = _mock_create_fn(captured)
            score_articles([_make_article(source_name="TechCrunch")],
                           datetime(2026, 3, 16, 12, 0, tzinfo=timezone.utc))

        assert captured[0]["source"] == "TechCrunch"
        assert "source_name" not in captured[0]

    def test_all_expected_fields_present(self):
        """Each article in the prompt has exactly the fields the spec requires."""
        captured = []
        with patch("agent.scorer.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create = _mock_create_fn(captured)
            score_articles([_make_article()],
                           datetime(2026, 3, 16, 12, 0, tzinfo=timezone.utc))

        expected_keys = {"id", "title", "source", "category", "published_iso", "summary", "url"}
        assert set(captured[0].keys()) == expected_keys

    def test_summary_truncated_to_300_chars(self):
        """Long summaries are capped at 300 characters."""
        captured = []
        with patch("agent.scorer.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create = _mock_create_fn(captured)
            score_articles([_make_article(summary="x" * 500)],
                           datetime(2026, 3, 16, 12, 0, tzinfo=timezone.utc))

        assert len(captured[0]["summary"]) == 300

    def test_missing_published_uses_now(self):
        """Articles without a published date fall back to current time."""
        now = datetime(2026, 3, 16, 12, 0, tzinfo=timezone.utc)
        captured = []
        with patch("agent.scorer.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create = _mock_create_fn(captured)
            score_articles([_make_article(published=None)], now)

        assert captured[0]["published_iso"] == now.isoformat()

    def test_scored_articles_have_metadata(self):
        """Returned articles include scores, total_score, reasoning, cluster_sources."""
        captured = []
        with patch("agent.scorer.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create = _mock_create_fn(captured)
            result = score_articles([_make_article()],
                                    datetime(2026, 3, 16, 12, 0, tzinfo=timezone.utc))

        article = result[0]
        assert "scores" in article
        assert "total_score" in article
        assert "reasoning" in article
        assert "cluster_sources" in article
        # Original fields preserved
        assert article["source_name"] == "SVT Nyheter"
        assert article["title"] == "Test headline"

    def test_scores_per_category(self):
        """Articles from different categories are scored separately."""
        call_count = {"n": 0}
        captured = []

        def counting_create(**kwargs):
            call_count["n"] += 1
            return _mock_create_fn(captured)(**kwargs)

        articles = [
            _make_article(category="Tech", title="Tech story"),
            _make_article(category="Sweden", title="Sweden story", url="https://example.com/2"),
        ]
        with patch("agent.scorer.anthropic.Anthropic") as MockClient:
            MockClient.return_value.messages.create = counting_create
            result = score_articles(articles, datetime(2026, 3, 16, 12, 0, tzinfo=timezone.utc))

        assert call_count["n"] == 2  # one call per category
        assert len(result) == 2


class TestParseJson:
    """Verify _parse_json handles various Claude response formats."""

    def test_plain_json(self):
        result = _parse_json('{"selected": []}')
        assert result == {"selected": []}

    def test_markdown_fenced_json(self):
        raw = '```json\n{"selected": []}\n```'
        result = _parse_json(raw)
        assert result == {"selected": []}

    def test_markdown_fenced_no_lang(self):
        raw = '```\n{"selected": []}\n```'
        result = _parse_json(raw)
        assert result == {"selected": []}

    def test_preamble_before_json(self):
        raw = 'Here is the result:\n\n{"selected": []}'
        result = _parse_json(raw)
        assert result == {"selected": []}

    def test_empty_string_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_json("")

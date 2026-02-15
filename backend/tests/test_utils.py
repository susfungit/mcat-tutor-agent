"""Unit tests for json_parser, mcat_topics, and socratic prompt builder."""

import pytest

from app.utils.json_parser import parse_llm_json, JSONParseError
from app.utils.mcat_topics import (
    list_sections,
    list_topics,
    list_subtopics,
    search_topics,
    validate_topic,
)
from app.prompts.socratic import build_socratic_prompt


# ── json_parser ──────────────────────────────────────────────────────

class TestParseLLMJson:
    def test_plain_json(self):
        assert parse_llm_json('{"a": 1}') == {"a": 1}

    def test_json_with_whitespace(self):
        assert parse_llm_json('  \n {"b": 2} \n ') == {"b": 2}

    def test_json_in_code_fence(self):
        text = '```json\n{"c": 3}\n```'
        assert parse_llm_json(text) == {"c": 3}

    def test_json_in_bare_code_fence(self):
        text = '```\n{"d": 4}\n```'
        assert parse_llm_json(text) == {"d": 4}

    def test_json_with_surrounding_text(self):
        text = 'Here is the result:\n```json\n{"e": 5}\n```\nDone!'
        assert parse_llm_json(text) == {"e": 5}

    def test_json_array(self):
        assert parse_llm_json("[1, 2, 3]") == [1, 2, 3]

    def test_invalid_json_raises(self):
        with pytest.raises(JSONParseError):
            parse_llm_json("this is not json at all")

    def test_empty_string_raises(self):
        with pytest.raises(JSONParseError):
            parse_llm_json("")

    def test_nested_json(self):
        text = '{"options": {"A": "yes", "B": "no"}, "correct": "A"}'
        result = parse_llm_json(text)
        assert result["correct"] == "A"
        assert result["options"]["A"] == "yes"


# ── mcat_topics ──────────────────────────────────────────────────────

class TestMCATTopics:
    def test_list_sections_returns_four(self):
        sections = list_sections()
        assert len(sections) == 4
        assert "Critical Analysis and Reasoning Skills" in sections

    def test_list_topics_valid_section(self):
        topics = list_topics("Chemical and Physical Foundations of Biological Systems")
        assert "General Chemistry" in topics
        assert "Physics" in topics

    def test_list_topics_invalid_section(self):
        with pytest.raises(KeyError):
            list_topics("Nonexistent Section")

    def test_list_subtopics(self):
        subtopics = list_subtopics(
            "Biological and Biochemical Foundations of Living Systems",
            "Biochemistry",
        )
        assert "Enzyme Kinetics" in subtopics

    def test_list_subtopics_invalid_topic(self):
        with pytest.raises(KeyError):
            list_subtopics(
                "Chemical and Physical Foundations of Biological Systems", "Fake Topic"
            )

    def test_search_topics_finds_match(self):
        results = search_topics("enzyme")
        assert len(results) > 0
        assert any("Enzyme" in r.get("subtopic", "") or "Enzyme" in r.get("topic", "") for r in results)

    def test_search_topics_case_insensitive(self):
        results_lower = search_topics("kinetics")
        results_upper = search_topics("KINETICS")
        assert len(results_lower) == len(results_upper)

    def test_search_topics_no_match(self):
        results = search_topics("xyznonexistent")
        assert results == []

    def test_validate_topic_true(self):
        assert validate_topic(
            "Chemical and Physical Foundations of Biological Systems",
            "General Chemistry",
        )

    def test_validate_topic_false_section(self):
        assert not validate_topic("Fake Section", "General Chemistry")

    def test_validate_topic_false_topic(self):
        assert not validate_topic(
            "Chemical and Physical Foundations of Biological Systems", "Fake Topic"
        )


# ── socratic prompt ──────────────────────────────────────────────────

class TestSocraticPrompt:
    def test_builds_prompt_with_level(self):
        prompt = build_socratic_prompt("Section", "Topic", "Concept", 1)
        assert "Level 1" in prompt
        assert "Open Exploration" in prompt
        assert "Section" in prompt
        assert "Topic" in prompt
        assert "Concept" in prompt

    def test_escalation_levels_1_through_5(self):
        for level in range(1, 6):
            prompt = build_socratic_prompt("S", "T", "C", level)
            assert f"Level {level}" in prompt

    def test_clamps_below_1(self):
        prompt = build_socratic_prompt("S", "T", "C", 0)
        assert "Level 1" in prompt

    def test_clamps_above_5(self):
        prompt = build_socratic_prompt("S", "T", "C", 10)
        assert "Level 5" in prompt

    def test_level_5_mentions_direct_teaching(self):
        prompt = build_socratic_prompt("S", "T", "C", 5)
        assert "Direct Teaching" in prompt

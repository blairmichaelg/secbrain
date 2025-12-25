from secbrain.utils.response_diff import (
    _entropy,
    _normalize_headers,
    diff_body_size_entropy,
    diff_headers,
    diff_json_semantic,
    diff_keywords,
    diff_status,
)


def test_diff_status():
    assert diff_status(200, 200)["changed"] is False
    assert diff_status(200, 403)["changed"] is True
    assert diff_status(200, 200)["baseline"] == 200
    assert diff_status(200, 403)["test"] == 403


def test_normalize_headers():
    """Test header normalization to lowercase."""
    headers = {"Content-Type": "application/json", "X-Custom": "value"}
    normalized = _normalize_headers(headers)
    assert normalized == {"content-type": "application/json", "x-custom": "value"}


def test_diff_headers():
    res = diff_headers({"A": "1"}, {"a": "2", "b": "3"})
    assert res["has_diff"] is True
    assert "a" in res["changed"]
    assert "b" in res["added"]
    assert "a" not in res["removed"]


def test_diff_headers_removed():
    """Test headers that are removed."""
    res = diff_headers({"A": "1", "B": "2"}, {"a": "1"})
    assert res["has_diff"] is True
    assert "b" in res["removed"]
    assert res["removed"]["b"] == "2"


def test_diff_headers_no_diff():
    """Test headers with no differences."""
    res = diff_headers({"A": "1", "B": "2"}, {"a": "1", "b": "2"})
    assert res["has_diff"] is False
    assert res["added"] == {}
    assert res["removed"] == {}
    assert res["changed"] == {}


def test_entropy_empty_string():
    """Test entropy calculation with empty string."""
    assert _entropy("") == 0.0


def test_entropy_single_char():
    """Test entropy with single repeated character."""
    # All same character = low entropy
    result = _entropy("aaaa")
    assert result == 0.0  # Only one unique character


def test_entropy_varied_chars():
    """Test entropy with varied characters."""
    # More variety = higher entropy
    result = _entropy("abcd")
    assert result > 0.0


def test_diff_body_size_entropy():
    res = diff_body_size_entropy("aaa", "aaab")
    assert res["size"]["delta"] == 1
    assert res["entropy"]["test"] >= res["entropy"]["baseline"]
    assert res["size"]["baseline"] == 3
    assert res["size"]["test"] == 4


def test_diff_body_size_entropy_empty():
    """Test body diff with empty strings."""
    res = diff_body_size_entropy("", "")
    assert res["size"]["delta"] == 0
    assert res["entropy"]["baseline"] == 0.0
    assert res["entropy"]["test"] == 0.0


def test_diff_keywords():
    res = diff_keywords("hello", "hello admin", ["admin", "forbidden"])
    assert res["changed"] is True
    assert res["keywords"]["admin"]["baseline"] is False
    assert res["keywords"]["admin"]["test"] is True


def test_diff_keywords_no_change():
    """Test keywords with no changes."""
    res = diff_keywords("hello admin", "hello admin", ["admin", "forbidden"])
    assert res["changed"] is False
    assert res["keywords"] == {}


def test_diff_keywords_removal():
    """Test keyword removal."""
    res = diff_keywords("hello admin", "hello", ["admin"])
    assert res["changed"] is True
    assert res["keywords"]["admin"]["baseline"] is True
    assert res["keywords"]["admin"]["test"] is False


def test_diff_json_semantic():
    res = diff_json_semantic('{"a":1}', '{"a":1,"b":2}')
    assert res["changed"] is True
    assert "b" in res["added_keys"]


def test_diff_json_semantic_removed_keys():
    """Test JSON with removed keys."""
    res = diff_json_semantic('{"a":1,"b":2}', '{"a":1}')
    assert res["changed"] is True
    assert "b" in res["removed_keys"]


def test_diff_json_semantic_no_change():
    """Test JSON with no changes."""
    res = diff_json_semantic('{"a":1}', '{"a":1}')
    assert res["changed"] is False
    assert res["added_keys"] == []
    assert res["removed_keys"] == []


def test_diff_json_semantic_invalid_json():
    """Test JSON diff with invalid JSON."""
    res = diff_json_semantic("not json", "also not json")
    assert res["changed"] is False
    assert res["error"] == "non-json"


def test_diff_json_semantic_empty_strings():
    """Test JSON diff with empty strings."""
    res = diff_json_semantic("", "")
    assert res["changed"] is False


def test_diff_json_semantic_non_dict_json():
    """Test JSON diff with non-dict JSON (lists)."""
    res = diff_json_semantic('[1,2,3]', '[1,2,3,4]')
    assert res["changed"] is True
    assert res["added_keys"] == []  # Lists don't have keys
    assert res["removed_keys"] == []

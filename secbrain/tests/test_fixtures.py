"""Tests for contract fixtures."""

from pathlib import Path

from secbrain.fixtures.contract_fixtures import load_fixtures_from_file


class TestLoadFixturesFromFile:
    """Test the load_fixtures_from_file function."""

    def test_load_valid_json_list(self, tmp_path: Path) -> None:
        """Test loading valid JSON list of fixtures."""
        fixture_file = tmp_path / "fixtures.json"
        fixture_file.write_text('[{"name": "test1"}, {"name": "test2"}]')
        
        result = load_fixtures_from_file(fixture_file)
        assert len(result) == 2
        assert result[0]["name"] == "test1"
        assert result[1]["name"] == "test2"

    def test_load_empty_list(self, tmp_path: Path) -> None:
        """Test loading empty JSON list."""
        fixture_file = tmp_path / "empty.json"
        fixture_file.write_text('[]')
        
        result = load_fixtures_from_file(fixture_file)
        assert result == []

    def test_load_nonexistent_file(self) -> None:
        """Test loading nonexistent file returns empty list."""
        result = load_fixtures_from_file("/nonexistent/path/file.json")
        assert result == []

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Test loading invalid JSON returns empty list."""
        fixture_file = tmp_path / "invalid.json"
        fixture_file.write_text('not valid json')
        
        result = load_fixtures_from_file(fixture_file)
        assert result == []

    def test_load_json_dict_not_list(self, tmp_path: Path) -> None:
        """Test loading JSON dict instead of list returns empty list."""
        fixture_file = tmp_path / "dict.json"
        fixture_file.write_text('{"key": "value"}')
        
        result = load_fixtures_from_file(fixture_file)
        assert result == []

    def test_load_with_string_path(self, tmp_path: Path) -> None:
        """Test loading with string path instead of Path object."""
        fixture_file = tmp_path / "fixtures.json"
        fixture_file.write_text('[{"test": "data"}]')
        
        result = load_fixtures_from_file(str(fixture_file))
        assert len(result) == 1
        assert result[0]["test"] == "data"

    def test_load_filters_non_dict_items(self, tmp_path: Path) -> None:
        """Test that non-dict items are filtered out."""
        fixture_file = tmp_path / "mixed.json"
        fixture_file.write_text('[{"valid": "dict"}, "string", 123, null, {"another": "dict"}]')
        
        result = load_fixtures_from_file(fixture_file)
        assert len(result) == 2
        assert result[0]["valid"] == "dict"
        assert result[1]["another"] == "dict"

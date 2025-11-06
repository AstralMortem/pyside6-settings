import pytest
from datetime import date, datetime
from pathlib import Path
from urllib.parse import ParseResult
from pyside6_settings.type_parser import TypeParser


class TestTypeParserInit:
    """Test TypeParser initialization and default parsers"""

    def test_init_creates_empty_dicts(self):
        parser = TypeParser()
        assert isinstance(parser._parsers, dict)
        assert isinstance(parser._serializers, dict)
        assert isinstance(parser._type_mapping, dict)

    def test_default_parsers_registered(self):
        parser = TypeParser()
        assert "path" in parser._parsers
        assert "date" in parser._parsers
        assert "datetime" in parser._parsers
        assert "url" in parser._parsers

    def test_default_serializers_registered(self):
        parser = TypeParser()
        assert "path" in parser._serializers
        assert "date" in parser._serializers
        assert "datetime" in parser._serializers
        assert "url" in parser._serializers

    def test_default_type_mapping_registered(self):
        parser = TypeParser()
        assert parser._type_mapping["path"] == Path
        assert parser._type_mapping["date"] == date
        assert parser._type_mapping["datetime"] == datetime
        assert parser._type_mapping["url"] == ParseResult


class TestRegisterParser:
    """Test custom parser registration"""

    def test_register_parser_minimal(self):
        parser = TypeParser()
        custom_parser = lambda x: x.upper()
        parser.register_parser("uppercase", custom_parser)

        assert "uppercase" in parser._parsers
        assert parser._parsers["uppercase"] == custom_parser

    def test_register_parser_with_serializer(self):
        parser = TypeParser()
        custom_parser = lambda x: x.upper()
        custom_serializer = lambda x: x.lower()

        parser.register_parser("uppercase", custom_parser, custom_serializer)

        assert "uppercase" in parser._parsers
        assert "uppercase" in parser._serializers

    def test_register_parser_with_type_mapping(self):
        parser = TypeParser()

        class CustomType:
            pass

        parser.register_parser(
            "custom", lambda x: CustomType(), lambda x: "custom", CustomType
        )

        assert parser._type_mapping["custom"] == CustomType

    def test_register_parser_overwrites_existing(self):
        parser = TypeParser()
        new_parser = lambda x: "new"

        parser.register_parser("date", new_parser)
        assert parser._parsers["date"] == new_parser


class TestParseValue:
    """Test parsing values with @ prefix"""

    def test_parse_plain_string(self):
        parser = TypeParser()
        result = parser.parse_value("plain string")
        assert result == "plain string"

    def test_parse_plain_int(self):
        parser = TypeParser()
        result = parser.parse_value(42)
        assert result == 42

    def test_parse_path(self):
        parser = TypeParser()
        result = parser.parse_value("@path /home/user/file.txt")
        assert isinstance(result, Path)
        assert str(result) == "/home/user/file.txt"

    def test_parse_date(self):
        parser = TypeParser()
        result = parser.parse_value("@date 2024-01-15")
        assert isinstance(result, date)
        assert result == date(2024, 1, 15)

    def test_parse_datetime(self):
        parser = TypeParser()
        result = parser.parse_value("@datetime 2024-01-15T10:30:00")
        assert isinstance(result, datetime)
        assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_parse_url(self):
        parser = TypeParser()
        result = parser.parse_value("@url https://example.com/path")
        assert isinstance(result, ParseResult)
        assert result.scheme == "https"
        assert result.netloc == "example.com"
        assert result.path == "/path"

    def test_parse_at_without_space(self):
        parser = TypeParser()
        result = parser.parse_value("@notaparser")
        assert result == "@notaparser"

    def test_parse_unknown_keyword(self):
        parser = TypeParser()
        result = parser.parse_value("@unknown some data")
        assert result == "@unknown some data"

    def test_parse_dict_with_nested_values(self):
        parser = TypeParser()
        data = {
            "name": "test",
            "created": "@date 2024-01-15",
            "path": "@path /tmp/file",
        }
        result = parser.parse_value(data)

        assert result["name"] == "test"
        assert isinstance(result["created"], date)
        assert isinstance(result["path"], Path)

    def test_parse_list_with_mixed_values(self):
        parser = TypeParser()
        data = ["plain", "@date 2024-01-15", 42, "@path /tmp"]
        result = parser.parse_value(data)

        assert result[0] == "plain"
        assert isinstance(result[1], date)
        assert result[2] == 42
        assert isinstance(result[3], Path)

    def test_parse_nested_dict_and_list(self):
        parser = TypeParser()
        data = {"items": [{"date": "@date 2024-01-15"}, {"date": "@date 2024-01-16"}]}
        result = parser.parse_value(data)

        assert isinstance(result["items"][0]["date"], date)
        assert isinstance(result["items"][1]["date"], date)

    def test_parse_custom_registered_parser(self):
        parser = TypeParser()
        parser.register_parser("upper", lambda x: x.upper())

        result = parser.parse_value("@upper hello")
        assert result == "HELLO"


class TestSerializeValue:
    """Test serialization of Python objects back to string format"""

    def test_serialize_plain_string(self):
        parser = TypeParser()
        result = parser.serialize_value("plain")
        assert result == "plain"

    def test_serialize_plain_int(self):
        parser = TypeParser()
        result = parser.serialize_value(42)
        assert result == 42

    def test_serialize_date(self):
        parser = TypeParser()
        d = date(2024, 1, 15)
        result = parser.serialize_value(d)
        assert result == "@date 2024-01-15"

    def test_serialize_datetime(self):
        parser = TypeParser()
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = parser.serialize_value(dt)
        assert result == "@date 2024-01-15T10:30:00"

    def test_serialize_path(self):
        parser = TypeParser()
        p = Path("/home/user/file.txt")
        result = parser.serialize_value(p)
        assert result == "@path /home/user/file.txt"

    def test_serialize_url(self):
        parser = TypeParser()
        from urllib.parse import urlparse

        url = urlparse("https://example.com/path")
        result = parser.serialize_value(url)
        assert result == "@url https://example.com/path"

    def test_serialize_with_explicit_keyword(self):
        parser = TypeParser()
        result = parser.serialize_value(date(2024, 1, 15), keyword="date")
        assert result == "@date 2024-01-15"

    def test_serialize_dict_with_nested_values(self):
        parser = TypeParser()
        data = {"name": "test", "created": date(2024, 1, 15), "path": Path("/tmp/file")}
        result = parser.serialize_value(data)

        assert result["name"] == "test"
        assert result["created"] == "@date 2024-01-15"
        assert result["path"] == "@path /tmp/file"

    def test_serialize_list_with_mixed_values(self):
        parser = TypeParser()
        data = ["plain", date(2024, 1, 15), 42, Path("/tmp")]
        result = parser.serialize_value(data)

        assert result[0] == "plain"
        assert result[1] == "@date 2024-01-15"
        assert result[2] == 42
        assert result[3] == "@path /tmp"

    def test_serialize_nested_structures(self):
        parser = TypeParser()
        data = {"items": [{"date": date(2024, 1, 15)}, {"date": date(2024, 1, 16)}]}
        result = parser.serialize_value(data)

        assert result["items"][0]["date"] == "@date 2024-01-15"
        assert result["items"][1]["date"] == "@date 2024-01-16"


class TestEncodeSerializedValue:
    """Test the _encode_serialized_value helper method"""

    def test_encode_plain_value(self):
        parser = TypeParser()
        result = parser._encode_serialized_value("2024-01-15", "date")
        assert result == "@date 2024-01-15"

    def test_encode_value_already_with_keyword(self):
        parser = TypeParser()
        result = parser._encode_serialized_value("@date 2024-01-15", "date")
        assert result == "@date 2024-01-15"

    def test_encode_value_with_keyword_as_prefix(self):
        parser = TypeParser()
        result = parser._encode_serialized_value("date 2024-01-15", "date")
        assert result == "@date 2024-01-15"

    def test_encode_value_with_at_but_different_keyword(self):
        parser = TypeParser()
        result = parser._encode_serialized_value("@other 2024-01-15", "date")
        assert result == "@other 2024-01-15"

    def test_encode_empty_string(self):
        parser = TypeParser()
        result = parser._encode_serialized_value("", "test")
        assert result == "@test "


class TestRoundTrip:
    """Test parsing and serializing round-trip"""

    def test_roundtrip_date(self):
        parser = TypeParser()
        original = "@date 2024-01-15"
        parsed = parser.parse_value(original)
        serialized = parser.serialize_value(parsed)
        assert serialized == original

    def test_roundtrip_datetime(self):
        parser = TypeParser()
        original = "@datetime 2024-01-15T10:30:00"
        parsed = parser.parse_value(original)
        serialized = parser.serialize_value(parsed, keyword="datetime")
        assert serialized == original

    def test_roundtrip_path(self):
        parser = TypeParser()
        original = "@path /home/user/file.txt"
        parsed = parser.parse_value(original)
        serialized = parser.serialize_value(parsed)
        assert serialized == original

    def test_roundtrip_url(self):
        parser = TypeParser()
        original = "@url https://example.com/path"
        parsed = parser.parse_value(original)
        serialized = parser.serialize_value(parsed)
        assert serialized == original

    def test_roundtrip_complex_dict(self):
        parser = TypeParser()
        original = {
            "name": "test",
            "dates": ["@date 2024-01-15", "@date 2024-01-16"],
            "config": {"path": "@path /tmp", "url": "@url https://example.com"},
        }
        parsed = parser.parse_value(original)
        serialized = parser.serialize_value(parsed)

        # Verify structure is preserved
        assert serialized["name"] == "test"
        assert len(serialized["dates"]) == 2
        assert serialized["dates"][0] == "@date 2024-01-15"
        assert serialized["config"]["path"] == "@path /tmp"


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_parse_malformed_date(self):
        parser = TypeParser()
        with pytest.raises(ValueError):
            parser.parse_value("@date not-a-date")

    def test_parse_malformed_datetime(self):
        parser = TypeParser()
        with pytest.raises(ValueError):
            parser.parse_value("@datetime not-a-datetime")

    def test_parse_none_value(self):
        parser = TypeParser()
        result = parser.parse_value(None)
        assert result is None

    def test_serialize_none_value(self):
        parser = TypeParser()
        result = parser.serialize_value(None)
        assert result is None

    def test_parse_empty_string(self):
        parser = TypeParser()
        result = parser.parse_value("")
        assert result == ""

    def test_parse_at_only(self):
        parser = TypeParser()
        result = parser.parse_value("@")
        assert result == "@"

    def test_serialize_unknown_type(self):
        parser = TypeParser()

        class UnknownType:
            pass

        obj = UnknownType()
        result = parser.serialize_value(obj)
        # Should return the object unchanged if no serializer found
        assert result == obj

    def test_parse_empty_dict(self):
        parser = TypeParser()
        result = parser.parse_value({})
        assert result == {}

    def test_parse_empty_list(self):
        parser = TypeParser()
        result = parser.parse_value([])
        assert result == []

    def test_datetime_with_timezone(self):
        parser = TypeParser()
        dt_str = "@datetime 2024-01-15T10:30:00+01:00"
        parsed = parser.parse_value(dt_str)
        assert isinstance(parsed, datetime)

    def test_windows_path(self):
        parser = TypeParser()
        result = parser.parse_value("@path C:\\Users\\test\\file.txt")
        assert isinstance(result, Path)
        assert str(result) == "C:\\Users\\test\\file.txt"


class TestCustomParserIntegration:
    """Test custom parser registration and usage"""

    def test_custom_parser_parse_and_serialize(self):
        parser = TypeParser()

        # Register uppercase parser
        parser.register_parser("upper", lambda x: x.upper(), lambda x: x.lower(), str)

        # Parse
        result = parser.parse_value("@upper hello")
        assert result == "HELLO"

        # Serialize with explicit keyword
        serialized = parser.serialize_value("HELLO", keyword="upper")
        assert serialized == "@upper hello"

    def test_custom_complex_type(self):
        parser = TypeParser()

        class Coordinate:
            def __init__(self, x: float, y: float):
                self.x = x
                self.y = y

        def parse_coord(s: str) -> Coordinate:
            x, y = map(float, s.split(","))
            return Coordinate(x, y)

        def serialize_coord(c: Coordinate) -> str:
            return f"{c.x},{c.y}"

        parser.register_parser("coord", parse_coord, serialize_coord, Coordinate)

        # Parse
        result = parser.parse_value("@coord 1.5,2.5")
        assert isinstance(result, Coordinate)
        assert result.x == 1.5
        assert result.y == 2.5

        # Serialize
        serialized = parser.serialize_value(result)
        assert serialized == "@coord 1.5,2.5"

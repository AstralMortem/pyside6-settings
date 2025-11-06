from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type
from urllib.parse import urlparse, ParseResult


# Default parsers and serializers
def _parse_date(s: str):
    return datetime.fromisoformat(s).date()


def _serialize_date(d) -> str:
    return str(d.isoformat())


def _parse_datetime(s: str):
    return datetime.fromisoformat(s)


def _serialize_datetime(dt: datetime) -> str:
    return str(dt.isoformat())


def _serialize_url(url) -> str:
    return str(url.geturl())


class TypeParser:
    def __init__(self):
        self._parsers: Dict[str, Callable[[str], Any]] = {}
        self._serializers: Dict[str, Callable[..., str]] = {}
        self._type_mapping: Dict[str, Type[Any]] = {}

        # Register default parsers
        self.register_parser("path", Path, str, Path)
        self.register_parser("date", _parse_date, _serialize_date, date)
        self.register_parser("datetime", _parse_datetime, _serialize_datetime, datetime)
        self.register_parser("url", urlparse, _serialize_url, ParseResult)

    def register_parser(
        self,
        keyword: str,
        parser: Callable[[str], Any],
        serializer: Optional[Callable[..., str]] = None,
        python_type: Optional[Type[Any]] = None,
    ):
        self._parsers[keyword] = parser
        if serializer:
            self._serializers[keyword] = serializer
        if python_type:
            self._type_mapping[keyword] = python_type

    def parse_value(self, value: Any) -> Any:
        """Parse a value that might have @ prefix"""
        if isinstance(value, str) and value.startswith("@"):
            parts = value.split(" ", 1)
            if len(parts) == 2:
                keyword, data = parts
                keyword = keyword[1:]  # Remove @
                if keyword in self._parsers:
                    return self._parsers[keyword](data)
        elif isinstance(value, dict):
            return {k: self.parse_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.parse_value(v) for v in value]
        return value

    def serialize_value(self, value: Any, keyword: Optional[str] = None) -> Any:
        """Serialize a Python object back to format"""
        # If keyword is explicitly provided, use it
        if keyword and keyword in self._serializers:
            value = self._serializers[keyword](value)
            return self._encode_serialized_value(value, keyword)
        # Auto-detect type and serialize
        value_type = type(value)

        for kw, py_type in self._type_mapping.items():
            if value_type == py_type or isinstance(value, py_type):
                if kw in self._serializers:
                    value = self._serializers[kw](value)
                    return self._encode_serialized_value(value, kw)

        # Handle collections recursively
        if isinstance(value, dict):
            return {k: self.serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.serialize_value(v) for v in value]

        return value

    def _encode_serialized_value(self, value: str, keyword: str) -> str:
        """Check if serialized value with keyword, set keyword if need"""
        if value.startswith("@" + keyword):
            return value
        # check if keyword is not part of value by whitespace
        if value.startswith(keyword + " "):
            return f"@{value}"
        if not value.startswith("@"):
            return f"@{keyword} {value}"
        return value

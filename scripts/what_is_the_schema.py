import json
from collections import defaultdict
from typing import Dict, Set, Any, Union
from datetime import datetime
import re
from rich import print
from rich.console import Console
from rich.syntax import Syntax


class JSONSchemaAnalyzer:
    def __init__(self):
        self.schema_structure = {}
        self.max_unique_samples = 10
        self.date_counters = defaultdict(int)

    def _get_type_name(self, value: Any) -> str:
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        return str(type(value).__name__)

    def _is_date(self, key: str) -> bool:
        """Check if a string is a date in various formats."""
        date_patterns = [
            '%Y-%m-%d',  # 2021-11-08
            '%d-%m-%Y',  # 08-11-2021
            '%Y/%m/%d',  # 2021/11/08
            '%d/%m/%Y',  # 08/11/2021
            '%Y%m%d',  # 20211108
            '%d%m%Y',  # 08112021
            '%B %d, %Y',  # November 08, 2021
            '%d %B %Y',  # 08 November 2021
            '%Y-%m',  # 2021-11
            '%m-%Y',  # 11-2021
        ]

        for pattern in date_patterns:
            try:
                datetime.strptime(key, pattern)
                return True
            except ValueError:
                continue
        return False

    def _normalize_path(self, path: str) -> str:
        """Convert date-based keys to a normalized format."""
        if not path:
            return path

        parts = path.split('.')
        normalized_parts = []

        for part in parts:
            if self._is_date(part):
                level = len(normalized_parts)
                date_key = f"date_{level}"
                normalized_parts.append(date_key)
            else:
                normalized_parts.append(part)

        return '.'.join(normalized_parts)

    def _analyze_value(self, path: str, value: Any) -> None:
        """Recursively analyze a value and update statistics."""
        normalized_path = self._normalize_path(path)
        value_type = self._get_type_name(value)

        if normalized_path not in self.schema_structure:
            self.schema_structure[normalized_path] = {
                'type': value_type,
                'samples': set()
            }

        if not isinstance(value, (dict, list)) and len(
                self.schema_structure[normalized_path]['samples']) < self.max_unique_samples:
            self.schema_structure[normalized_path]['samples'].add(str(value))

        if isinstance(value, dict):
            for key, val in value.items():
                new_path = f"{path}.{key}" if path else key
                self._analyze_value(new_path, val)
        elif isinstance(value, list) and value:
            self._analyze_value(f"{normalized_path}[]", value[0])

    def analyze_json(self, json_data: Union[Dict, list]) -> None:
        if isinstance(json_data, list):
            for record in json_data[:1]:
                self._analyze_value("", record)
        else:
            first_record = next(iter(json_data.values()))
            self._analyze_value("", first_record)

    def _build_nested_schema(self) -> Dict:
        """Convert flat schema structure to nested dictionary."""

        def create_nested_dict(path_parts: list, value: Dict) -> Dict:
            if not path_parts:
                result = {'type': value['type']}
                if value['samples']:
                    result['examples'] = list(value['samples'])
                return result

            current_part = path_parts[0]
            remaining_parts = path_parts[1:]

            if current_part.endswith('[]'):
                current_part = current_part[:-2]
                return {
                    current_part: {
                        'type': 'array',
                        'items': create_nested_dict(remaining_parts, value)
                    }
                }
            else:
                nested = create_nested_dict(remaining_parts, value)
                return {
                    current_part: nested if not remaining_parts else {
                        'type': 'object',
                        'properties': nested
                    }
                }

        result = {}
        for path, info in sorted(self.schema_structure.items()):
            if not path:  # root level
                continue

            path_parts = path.split('.')
            current_dict = create_nested_dict(path_parts, info)

            # Merge with existing schema
            for key, value in current_dict.items():
                if key in result:
                    if 'properties' in result[key] and 'properties' in value:
                        result[key]['properties'].update(value['properties'])
                    else:
                        result[key].update(value)
                else:
                    result[key] = value

        return result

    def print_schema(self) -> None:
        """Print the clean schema as formatted JSON"""
        nested_schema = self._build_nested_schema()
        schema_json = json.dumps(nested_schema, indent=2)

        console = Console()
        syntax = Syntax(schema_json, "json", theme="monokai", line_numbers=True)
        console.print(syntax)


def analyze_json_file(file_path: str) -> JSONSchemaAnalyzer:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                data = json.load(f)

    analyzer = JSONSchemaAnalyzer()
    analyzer.analyze_json(data)
    return analyzer


if __name__ == "__main__":
    file_path = "../data/tinder_profiles_2021-11-10.json"
    analyzer = analyze_json_file(file_path)
    analyzer.print_schema()
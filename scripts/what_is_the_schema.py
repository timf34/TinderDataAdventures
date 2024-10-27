import json
from collections import defaultdict
from typing import Dict, Set, Any, Union
import pandas as pd
from rich import print
from rich.tree import Tree
from rich.console import Console
from rich.syntax import Syntax


class JSONSchemaAnalyzer:
    def __init__(self):
        self.schema_structure = {}
        self.max_unique_samples = 10

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

    def _collect_sample(self, path: str, value: Any) -> None:
        if not isinstance(value, (dict, list)) and path in self.schema_structure:
            samples = self.schema_structure[path].get('samples', set())
            if len(samples) < self.max_unique_samples:
                samples.add(str(value))
            self.schema_structure[path]['samples'] = samples

    def _analyze_value(self, path: str, value: Any) -> None:
        value_type = self._get_type_name(value)

        if path not in self.schema_structure:
            self.schema_structure[path] = {
                'type': value_type,
                'samples': set()
            }

        self._collect_sample(path, value)

        if isinstance(value, dict):
            for key, val in value.items():
                new_path = f"{path}.{key}" if path else key
                self._analyze_value(new_path, val)
        elif isinstance(value, list) and value:
            # For arrays, analyze structure of first element only
            self._analyze_value(f"{path}[]", value[0])

    def analyze_json(self, json_data: Union[Dict, list]) -> None:
        if isinstance(json_data, list):
            for record in json_data[:1]:  # Only analyze first record for structure
                self._analyze_value("", record)
        else:
            first_record = next(iter(json_data.values()))
            self._analyze_value("", first_record)

    def _build_nested_schema(self) -> Dict:
        """Convert flat schema structure to nested dictionary"""
        nested_schema = {}

        for path, info in sorted(self.schema_structure.items()):
            current = nested_schema
            if path:
                parts = path.split('.')
                for part in parts[:-1]:
                    if part.endswith('[]'):
                        part = part[:-2]  # Remove [] suffix
                    current = current.setdefault(part, {})
                last_part = parts[-1]
                if last_part.endswith('[]'):
                    last_part = last_part[:-2]  # Remove [] suffix
                    current[last_part] = {
                        'type': 'array',
                        'items': {'type': info['type']}
                    }
                else:
                    current[last_part] = {'type': info['type']}
                    if info['samples']:
                        current[last_part]['examples'] = list(info['samples'])

        return nested_schema

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
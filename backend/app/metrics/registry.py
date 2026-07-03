from __future__ import annotations

from app.metrics.plugins import PLUGINS


class MetricRegistry:
    def __init__(self):
        self.plugins = {plugin.id: plugin for plugin in PLUGINS}

    def get(self, plugin_id: str):
        return self.plugins.get(plugin_id)

    def describe_all(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for plugin in self.plugins.values():
            row: dict[str, object] = {
                "id":plugin.id,"version":plugin.version,"display_name":plugin.display_name,
                "description":plugin.description,"category":plugin.category,"direction":plugin.direction.value,
                "required_inputs":list(plugin.required_inputs),"optional_inputs":list(plugin.optional_inputs),
                "hardware_requirements":plugin.hardware_requirements,"dependency_requirements":list(plugin.dependency_requirements),
                "configuration_schema":plugin.configuration_schema or {},"result_schema":plugin.result_schema or {},
                "aggregation_strategy":plugin.aggregation_strategy,"limitations":plugin.limitations,"citation":plugin.citation,
            }
            rows.append(row)
        return rows


registry = MetricRegistry()

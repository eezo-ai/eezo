from .component import Component


class ComponentChart(Component):
    type = "chart"

    def __init__(self, chart_type, data, xaxis, name="", chart_title=""):
        super().__init__()

        possible_chart_types = [
            "donut",
            "pie",
            "heatmap",
            "radar",
            "polarArea",
            "radialBar",
            "bar-horizontal",
            "bar-stacked",
            "bar",
            "line-area",
            "line",
            "candlestick",
            "treemap",
            "scatter",
        ]
        if chart_type not in possible_chart_types:
            raise Exception(
                f"Invalid chart type '{chart_type}'. Possible chart types: {possible_chart_types}"
            )

        if chart_type in ["treemap"]:
            self.data = {
                "type": "chart",
                "chart_type": "treemap",
                "data": data,  # List of datapoints
                "labels": xaxis,
                "chart_title": str,
            }
        if chart_type in ["donut", "pie"]:
            self.data = {
                "type": "chart",
                "chart_type": chart_type,
                "data": [
                    {
                        "data": data,  # List of datapoints
                        "name": name,  # Legend
                    }
                ],
                "xaxis": xaxis,
                "chart_title": chart_title,
            }
        else:
            self.data = {
                "type": "chart",
                "chart_type": chart_type,
                "data": data,
                "xaxis": xaxis,
                "chart_title": chart_title,
            }

    def to_dict(self):
        return self.data

    @staticmethod
    def json_description() -> str:
        """
        Returns a markdown formatted string with the JSON schema for the chart component.
        use an LLM to generate the JSON schema for the chart component and
        add it as an UI component like:

        ```python
        example = {
            "type": "chart",
            "props": {
                "chart_type": "bar",  # or "donut", "pie", "heatmap", "radar", "polarArea", "radialBar", "bar-horizontal", "bar-stacked", "line-area", "line" etc.
                "data": [{"data": [10, 20, 30], "name": "Series 1"}],
                "xaxis": ["Jan", "Feb", "Mar"],
                "chart_title": "Bar Chart Title"
            }
        }

        m = contenxt.new_message()
        m.add(example["type"], example["props"])
        m.notify()
        ```
        """
        return """
## JSON Schema for Charts

### General JSON Chart Schema
{
  "type": "chart",
  "props": {
    "chart_type": "string",
    "data": "array",
    "xaxis": "array",
    "name": "string",
    "chart_title": "string"
  }
}

## Chart Types and Fields

### Donut, Pie, Polar Area, Radial Bar, Bar, Horizontal Bar, Stacked Bar, Line Area, Line, Radar, Heatmap Charts
#### Fields:
- chart_type: Type of the chart. Available options are "donut", "pie", "heatmap", "radar", "polarArea", "radialBar", "bar-horizontal", "bar-stacked", "bar", "line-area", "line", "candlestick", "treemap", "scatter"
- data: List of data series (or datapoints for donut and pie)
- xaxis: List of labels for each data point
- name: Legend for the chart (only for data series)
- chart_title: Title of the chart

#### Example:
ui_component_dict = {
    "type": "chart",
    "props": {
        "chart_type": "bar",  # or "donut", "pie", "heatmap", "radar", "polarArea", "radialBar", "bar-horizontal", "bar-stacked", "line-area", "line" etc.
        "data": [{"data": [10, 20, 30], "name": "Series 1"}],
        "xaxis": ["Jan", "Feb", "Mar"],
        "chart_title": "Bar Chart Title"
    }
}

### Candlestick Chart
#### Fields:
- chart_type: "candlestick"
- data: List of [open, high, low, close] data points
- xaxis: List of labels for each data point
- chart_title: Title of the chart

#### Example:
ui_component_dict = {
    "type": "chart",
    "props": {
        "chart_type": "candlestick",
        "data": [[20, 30, 10, 25], [40, 50, 30, 45]],
        "xaxis": ["Jan", "Feb"],
        "chart_title": "Candlestick Chart Title"
    }
}

### Treemap Chart
#### Fields:
- chart_type: "treemap"
- data: List of datapoints
- xaxis: List of labels for each data point
- chart_title: Title of the chart

#### Example:
ui_component_dict = {
    "type": "chart",
    "props": {
        "chart_type": "treemap",
        "data": [100, 200, 300],
        "xaxis": ["Item 1", "Item 2", "Item 3"],
        "chart_title": "Treemap Chart Title"
    }
}

### Scatter Chart
#### Fields:
- chart_type: "scatter"
- data: List of data series with each series having a list of [x, y] points
- xaxis: List of labels for each data point
- chart_title: Title of the chart

#### Example:
ui_component_dict = {
    "type": "chart",
    "props": {
        "chart_type": "scatter",
        "data": [{"data": [[10, 20], [30, 40]], "name": "Series 1"}],
        "xaxis": ["Jan", "Feb"],
        "chart_title": "Scatter Chart Title"
    }
}

## Example Usage for Different Chart Types
Each chart type follows the same pattern for creating the ui_component_dict with the corresponding chart_type, data, xaxis, name, and chart_title fields.
"""

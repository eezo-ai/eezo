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

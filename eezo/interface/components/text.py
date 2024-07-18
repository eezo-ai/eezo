from .component import Component


class ComponentText(Component):
    type = "text"

    def __init__(self, text: str):
        if not isinstance(text, str):
            raise ValueError("Text must be a string")
        super().__init__()
        self.text = text

    def to_dict(self):
        return {"type": self.type, "text": self.text}

    @staticmethod
    def json_description() -> str:
        """
        Returns a markdown formatted string with the JSON schema for the text component.

        ```python
        example = {
            "type": "text",
            "props": {
                "text": "Hello World!"
            }
        }

        m = context.new_message()
        m.add(example["type"], example["props"])
        m.notify()
        ```
        """
        return """
## JSON Schema for Text Component

### General JSON Schema
{
  "type": "text",
  "props": {
    "text": "string"
  }
}

### Fields:
- text: The main text content for this component

### Example:
ui_component_dict = {
    "type": "text",
    "props": {
        "text": "Hello World!"
    }
}

## Example Usage
Each text component follows the same pattern for creating the ui_component_dict with the corresponding text field.
"""

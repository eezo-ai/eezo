from .component import Component


class ComponentImage(Component):
    type = "image"

    def __init__(self, url: str):
        if not isinstance(url, str):
            raise ValueError("URL must be a string")
        super().__init__()
        self.url = url

    def to_dict(self):
        return {"type": self.type, "url": self.url}

    @staticmethod
    def json_description() -> str:
        """
        Returns a markdown formatted string with the JSON schema for the image component.

        ```python
        example = {
            "type": "image",
            "props": {
                "url": "https://example.com/image.jpg"
            }
        }

        m = context.new_message()
        m.add(example["type"], example["props"])
        m.notify()
        ```
        """
        return """
## JSON Schema for Image Component

### General JSON Schema
{
  "type": "image",
  "props": {
    "url": "string"
  }
}

### Fields:
- url: The URL of the image

### Example:
ui_component_dict = {
    "type": "image",
    "props": {
        "url": "https://example.com/image.jpg"
    }
}

## Example Usage
Each image component follows the same pattern for creating the ui_component_dict with the corresponding url field.
"""

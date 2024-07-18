from .component import Component


class ComponentYouTubeVideo(Component):
    type = "youtube_video"

    def __init__(self, video_id: str):
        if not isinstance(video_id, str):
            raise ValueError("Video ID must be a string")
        super().__init__()
        self.video_id = video_id

    def to_dict(self):
        return {"type": self.type, "video_id": self.video_id}

    @staticmethod
    def json_description() -> str:
        """
        Returns a markdown formatted string with the JSON schema for the YouTube video component.

        ```python
        example = {
            "type": "youtube_video",
            "props": {
                "video_id": "xyz123"
            }
        }

        m = context.new_message()
        m.add(example["type"], example["props"])
        m.notify()
        ```
        """
        return """
## JSON Schema for YouTube Video Component

### General JSON Schema
{
  "type": "youtube_video",
  "props": {
    "video_id": "string"
  }
}

### Fields:
- video_id: The ID of the YouTube video

### Example:
ui_component_dict = {
    "type": "youtube_video",
    "props": {
        "video_id": "xyz123"
    }
}

## Example Usage
Each YouTube video component follows the same pattern for creating the ui_component_dict with the corresponding video_id field.
"""

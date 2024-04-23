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

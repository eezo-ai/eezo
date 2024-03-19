from .component import Component


class ComponentText(Component):
    type = "text"

    def __init__(self, text):
        super().__init__()
        self.text = text

    def to_dict(self):
        return {"type": self.type, "text": self.text}

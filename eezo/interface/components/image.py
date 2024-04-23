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

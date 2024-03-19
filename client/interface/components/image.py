from .component import Component


class ComponentImage(Component):
    type = "image"

    def __init__(self, url):
        super().__init__()
        self.url = url

    def to_dict(self):
        return {"type": self.type, "url": self.url}

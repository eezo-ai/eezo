import uuid


class Component:
    def __init__(self, **kwargs):
        self.id = str(uuid.uuid4())

    def to_dict(self):
        raise NotImplementedError

    @staticmethod
    def json_description(self):
        raise NotImplementedError

from .components import Component, components
import uuid


class Message:
    def __init__(self, notify: callable = None):
        self.id = str(uuid.uuid4())
        self.notify: callable = notify
        self.interface: list[dict[str, Component]] = []

    def _create(self, _type, **kwargs):
        component_cls = components.get(_type)
        if not component_cls:
            raise Exception(f"Invalid component type '{_type}'")
        return {"type": _type, "component": component_cls(**kwargs)}

    def add(self, _type, **kwargs):
        component_dict = self._create(_type, **kwargs)
        self.interface.append(component_dict)
        return component_dict["component"]

    def remove(self, _id):
        self.interface = [i for i in self.interface if i["component"].id != _id]

    def replace(self, _id, _type, **kwargs):
        for i, item in enumerate(self.interface):
            if item["component"].id == _id:
                new_component_dict = self._create(_type, **kwargs)
                self.interface[i] = new_component_dict
                return new_component_dict["component"]
        raise Exception(f"Component with ID {_id} not found")

    def to_dict(self):
        return {
            "id": self.id,
            "interface": [c["component"].to_dict() for c in self.interface],
        }

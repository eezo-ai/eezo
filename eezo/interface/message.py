from typing import Callable, Dict, List, Optional, Type, Union, Any
from .components import Component, components
import uuid


class Message:
    def __init__(self, notify: Optional[Callable] = None):
        """
        Initializes a new Message instance with a unique identifier and an optional notification callback.

        Args:
            notify (Optional[Callable]): A callback function that is triggered to notify when a message needs to be sent.

        Attributes:
            id (str): A unique identifier for the message, generated using uuid.
            notify (Callable, optional): The callback function provided during initialization.
            interface (List[Dict[str, Component]]): A list of dictionaries holding components that make up the message content.
        """
        self.id: str = str(uuid.uuid4())
        self.notify: Optional[Callable] = notify
        self.interface: List[Dict[str, Component]] = []

    def _create(self, _type: str, **kwargs) -> Dict[str, Any]:
        """
        Creates a component dictionary from a specified type and keyword arguments.

        Args:
            _type (str): The type of component to create.
            **kwargs: Additional keyword arguments for initializing the component.

        Returns:
            Dict[str, Any]: A dictionary containing the type and the instantiated component object.

        Raises:
            Exception: If the specified type is not valid or recognized.

        This method looks up the component class from the components registry and instantiates it.
        """

        component_cls: Type[Component] = components.get(_type)
        if not component_cls:
            raise Exception(f"Invalid component type '{_type}'")
        return {"type": _type, "component": component_cls(**kwargs)}

    def add(self, _type: str, **kwargs) -> Component:
        """
        Adds a new component of the specified type to the message.

        Args:
            _type (str): The type of component to add.
            **kwargs: Keyword arguments necessary for creating the component.

        Returns:
            Component: The component instance that was added to the message.

        This method utilizes the _create method to generate and append a new component to the message's interface.
        """
        component_dict: Dict[str, Any] = self._create(_type, **kwargs)
        self.interface.append(component_dict)
        return component_dict["component"]

    def add_new_line(self) -> None:
        """
        Adds a new line component to the message.

        This method is a convenience function that adds a new line component to the message.
        """
        return self.add("text", text=" \n ")

    def remove(self, _id: str) -> None:
        """
        Removes a component from the message based on its unique identifier.

        Args:
            _id (str): The unique identifier of the component to remove.

        This method filters out the component with the given ID from the message's interface list.
        """
        self.interface = [i for i in self.interface if i["component"].id != _id]

    def replace(self, _id: str, _type: str, **kwargs) -> Component:
        """
        Replaces an existing component in the message with a new component of specified type and properties.

        Args:
            _id (str): The unique identifier of the component to replace.
            _type (str): The type of the new component to insert.
            **kwargs: Keyword arguments necessary for creating the new component.

        Returns:
            Component: The new component that replaces the old one.

        Raises:
            Exception: If no component with the specified ID is found.

        This method searches for the component with the given ID, replaces it with a new one, and returns the new component.
        """
        for i, item in enumerate(self.interface):
            if item["component"].id == _id:
                new_component_dict = self._create(_type, **kwargs)
                self.interface[i] = new_component_dict
                return new_component_dict["component"]
        raise Exception(f"Component with ID {_id} not found")

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the message and its components into a dictionary format suitable for serialization.

        Returns:
            Dict[str, Any]: A dictionary representation of the message, including its unique identifier and a list of components.

        This method is typically used when the message needs to be serialized for sending or storage.
        """
        return {
            "id": self.id,
            "interface": [c["component"].to_dict() for c in self.interface],
        }

from typing import Any, Dict, List, Type
from pydantic import BaseModel


class Agent(BaseModel):
    """
    Represents an agent within a system, capturing various configuration details and
    model specifications necessary for operation.

    Attributes:
        id (str): A unique identifier for the agent.
        input_model (Type[BaseModel]): The Pydantic model that defines the structure of input data the agent can handle.
        output_model (Type[BaseModel]): The Pydantic model that defines the structure of output data the agent produces.
        name (str): A human-readable name for the agent.
        description (str): A brief description of the agent and its purpose or functionality.
        status (str): The current operational status of the agent (e.g., 'active', 'inactive', 'training').
        properties_schema (Dict[str, Any]): A dictionary defining the properties that an agent's configuration can include.
        properties_required (List[str]): A list of property names that are required for the agent's configuration.
        return_schema (Dict[str, Any]): A dictionary defining the structure of data the agent returns after processing.

    Methods:
        to_dict: Converts the Agent instance into a dictionary, primarily for serialization purposes.
    """

    id: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    name: str
    description: str
    status: str
    properties_schema: Dict[str, Any]
    properties_required: List[str]
    return_schema: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Converts the instance of Agent to a dictionary representation.

        This can be particularly useful when you need to serialize the Agent instance to JSON,
        send it across a network, or save it to a database. The dictionary will include the
        id, name, description, status, properties_schema, properties_required, and return_schema of the agent.

        Returns:
            Dict[str, Any]: The dictionary representation of the agent.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "properties_schema": self.properties_schema,
            "properties_required": self.properties_required,
            "return_schema": self.return_schema,
        }

    def is_online(self) -> bool:
        """Check if the agent is online and available for processing.

        Returns:
            bool: True if the agent is online, False otherwise.
        """
        return self.status == "online"

    def llm_string(self) -> str:
        """Converts the instance of Agent to a string representation.

        This can be useful when you need to include information about this agent into a LLM prompt
        It is also useful to print or log the Agent instance.

        Returns:
            str: The string representation of the agent.
        """

        def format_dict(d, indent=0):
            """Recursively format a dictionary into a string with indentation to represent structure."""

            if not d:
                return "None"

            lines = []
            # Iterate over dictionary items
            for key, value in d.items():
                # Prepare the current line with proper indentation
                current_line = "  " * indent + f"- {key}:"
                if isinstance(value, dict):
                    # If the value is a dictionary, recursively format it
                    lines.append(current_line)
                    lines.append(format_dict(value, indent + 1))
                elif isinstance(value, list):
                    # If the value is a list, handle each item
                    lines.append(current_line)
                    for item in value:
                        if isinstance(item, dict):
                            # Recursively format dictionaries in lists
                            lines.append(format_dict(item, indent + 1))
                        else:
                            # Format other items directly
                            lines.append("  " * (indent + 1) + f"- {item}")
                else:
                    # Directly append other types (like strings, numbers)
                    lines.append(current_line + f" {value}")
            return "\n".join(lines)

        formatted_properties_schema = format_dict(self.properties_schema)
        if formatted_properties_schema is not "None":
            formatted_properties_schema = "\n" + formatted_properties_schema
        formatted_return_schema = format_dict(self.return_schema)
        if formatted_return_schema is not "None":
            formatted_return_schema = "\n" + formatted_return_schema

        if self.properties_required:
            formatted_properties_required = ", ".join(self.properties_required)
        else:
            formatted_properties_required = "None"

        return f"""
Agent ID: {self.id}
Name: {self.name}
Description: {self.description}
Status: {self.status}
Properties Schema: {formatted_properties_schema}
Properties Required: {formatted_properties_required}
Return Schema: {formatted_return_schema}
"""

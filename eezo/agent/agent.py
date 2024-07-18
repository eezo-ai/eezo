from typing import Any, Dict, List, Type
from pydantic import BaseModel, create_model, Field


class ModelFactory:
    """Factory for creating dynamic Pydantic models based on provided schemas and requirements."""

    @staticmethod
    def resolve_field_type(prop: Dict[str, Any], model_name: str = "Root") -> Type:
        """Resolve the Python type for a field property, recursively creating models for nested objects."""
        field_type = prop["type"]
        if field_type == "string":
            return str
        elif field_type == "integer":
            return int
        elif field_type == "array":
            item_type = ModelFactory.resolve_field_type(
                prop["items"], model_name + "Item"
            )
            return List[item_type]
        elif field_type == "object":
            nested_model_name = f"{model_name}_{ModelFactory.sanitize_name(next(iter(prop['properties'])))}"
            field_definitions = {
                key: (ModelFactory.resolve_field_type(value, nested_model_name), ...)
                for key, value in prop["properties"].items()
            }
            return create_model(nested_model_name, **field_definitions)
        else:
            raise ValueError(f"Unsupported type specified: {field_type}")

    @staticmethod
    def create_dynamic_model(
        name: str, properties: Dict[str, Any], required_fields: List[str]
    ) -> Type[BaseModel]:
        """Create a dynamic Pydantic model from properties schema and required fields."""
        if not properties:
            return create_model(name)

        fields = {
            prop: (
                ModelFactory.resolve_field_type(properties[prop], name),
                (
                    Field(..., description=properties[prop].get("description"))
                    if prop in required_fields
                    else Field(None, description=properties[prop].get("description"))
                ),
            )
            for prop in properties
        }
        return create_model(name, **fields)


class Agent(BaseModel):
    """
    Represents an agent within a system, capturing various configuration details and
    model specifications necessary for operation.

    Attributes:
        agent_id (str): A unique identifier for the agent.
        description (str): A brief description of the agent and its purpose or functionality.
        status (str): The current operational status of the agent (e.g., 'active', 'inactive', 'training').
        input_schema (Dict[str, Any]): A dictionary defining the properties that an agent's configuration can include.
        properties_required (List[str]): A list of property names that are required for the agent's configuration.
        environment_variables (Dict[str, Any]): A dictionary defining the environment variables that the agent requires.
        output_schema (Dict[str, Any]): A dictionary defining the structure of data the agent returns after processing.

    Methods:
        to_dict: Converts the Agent instance into a dictionary, primarily for serialization purposes.
    """

    agent_id: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    description: str
    status: str
    input_schema: Dict[str, Any]
    properties_required: List[str]
    environment_variables: Dict[str, Any]
    output_schema: Dict[str, Any]

    def __init__(self, **data: Any):
        """Initialize an instance of Agent, creating input and output models based on provided schemas."""

        input_model = ModelFactory.create_dynamic_model(
            data["agent_id"] + "_input",
            data["input_schema"],
            data["properties_required"],
        )
        output_model = ModelFactory.create_dynamic_model(
            data["agent_id"] + "_output",
            data["output_schema"],
            [],
        )
        data["input_model"] = input_model
        data["output_model"] = output_model
        if not "environment_variables" in data:
            data["environment_variables"] = {}
        super().__init__(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the instance of Agent to a dictionary representation.

        This can be particularly useful when you need to serialize the Agent instance to JSON,
        send it across a network, or save it to a database. The dictionary will include the
        agent_id, description, status, input_schema, properties_required, environment_variables, and output_schema of the agent.

        Returns:
            Dict[str, Any]: The dictionary representation of the agent.
        """
        return {
            "agent_id": self.agent_id,
            "description": self.description,
            "status": self.status,
            "input_schema": self.input_model.model_json_schema(),
            "properties_required": self.output_model.model_json_schema(),
            "environment_variables": self.environment_variables,
            "output_schema": self.output_schema,
        }

    def is_online(self) -> bool:
        """Check if the agent is online and available for processing.

        Returns:
            bool: True if the agent is online, False otherwise.
        """
        return self.status == "online"

    def llm_string(self) -> str:
        """Converts the instance of Agent to a string representation.

        This can be useful when you need to include information about this agent in an LLM prompt.
        It is also useful for printing or logging the Agent instance.

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

        formatted_input_schema = format_dict(self.input_model.model_json_schema())
        if formatted_input_schema != "None":
            formatted_input_schema = "\n" + formatted_input_schema
        formatted_output_schema = format_dict(self.output_model.model_json_schema())
        if formatted_output_schema != "None":
            formatted_output_schema = "\n" + formatted_output_schema

        if self.properties_required:
            formatted_properties_required = ", ".join(self.properties_required)
        else:
            formatted_properties_required = "None"

        formatted_environment_variables = format_dict(self.environment_variables)

        return f"""
Agent ID: {self.agent_id}
Description: {self.description}
Status: {self.status}
Properties Schema: {formatted_input_schema}
Properties Required: {formatted_properties_required}
Environment Variables: 
{formatted_environment_variables}
Return Schema: {formatted_output_schema}
"""

    @staticmethod
    def validate_json_schema(json_schema: dict) -> None:
        """Validate a JSON schema to ensure it is properly formatted and can be used to create a Pydantic model.

        Args:
            json_schema (Dict[str, Any]): A JSON schema to validate.

        Raises:
            ValueError: If the JSON schema is invalid or contains unsupported types.
        """
        if not isinstance(json_schema, dict):
            raise ValueError("JSON schema must be a dictionary.")

        try:
            ModelFactory.create_dynamic_model("temp", json_schema, [])
        except Exception as e:
            raise ValueError(f"Error validating JSON schema: {e}")

    @staticmethod
    def validate_environment_variables(env_vars: List[Dict[str, Any]]) -> None:
        """Validate environment variables to ensure they are properly formatted and can be used by the agent.

        Args:
            env_vars (List[Dict[str, Any]]): A list of dictionaries representing environment variables.

        Raises:
            ValueError: If the environment variables are not a list of dicts that contain a key and a value field.
        """
        try:
            if not isinstance(env_vars, list):
                raise ValueError(
                    "Environment variables must be a list of dictionaries."
                )

            if not all(
                isinstance(item, dict) and "key" in item and "value" in item
                for item in env_vars
            ):
                raise ValueError(
                    "Environment variables must be a list of dictionaries with 'key' and 'value' keys."
                )
        except Exception as e:
            raise ValueError(f"Error validating environment variables: {e}")

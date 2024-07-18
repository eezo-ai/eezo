from typing import Any, Dict, List

from .agent import Agent


class Agents:
    """
    A collection manager for `Agent` instances. It provides the capability to initialize a collection
    with predefined data, add new agents, and serialize the collection to a list of dictionaries.

    Attributes:
        agents (List[Agent]): A list of `Agent` instances that are currently managed by this collection.

    Methods:
        __init__: Constructs the `Agents` collection, optionally pre-populating it with agents.
        _add_agent: Adds a new `Agent` instance to the collection based on provided data.
        to_dict: Serializes the collection of `Agent` instances to a list of dictionaries.
    """

    def __init__(self, agents_data: List[Dict[str, Any]] = None):
        """
        Initializes a new `Agents` collection, which may be optionally pre-populated with agent data.

        Args:
            agents_data (List[Dict[str, Any]], optional): A list of dictionaries, each representing
            the data required to initialize an `Agent` instance.

        Each dictionary in the `agents_data` list should have the keys that correspond to the properties
        required to initialize an `Agent` instance, such as 'id' 'agent_id', 'description', etc.
        """
        self.agents: List[Agent] = []
        if agents_data:
            for agent_data in agents_data:
                print(agent_data)
                self._add_agent(agent_data)

    def _add_agent(self, agent_data: Dict[str, Any]):
        """
        Private method to add a new agent to the collection using the specified data.

        This method creates the input and output models dynamically using the ModelFactory based on the provided
        schema and required properties, then initializes an Agent instance with this data and appends it to the list.

        Args:
            agent_data (Dict[str, Any]): A dictionary containing all necessary data to create an Agent instance.
            This includes identifiers, model schemas, descriptions, statuses, and other relevant properties.
        """
        self.agents.append(Agent(**agent_data))

    def to_dict(self) -> List[Dict[str, Any]]:
        """
        Converts the collection of Agent instances into a list of dictionaries.

        This method is useful for serializing the Agents collection, such as for sending over a network
        or storing in a database.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing an Agent instance's data.
        """
        return [agent.to_dict() for agent in self.agents]

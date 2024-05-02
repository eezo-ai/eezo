from typing import Any, Dict, Iterator

import logging


class StateProxy:
    """
    Proxy class for managing the state data associated with a user session.

    This class provides a dictionary-like interface to the state, allowing items
    to be accessed, set, or deleted. It also handles loading and saving the state
    through the associated client.

    Attributes:
        client: The Client instance that this proxy is managing state for.
        _state: A dictionary that holds the state data.
    """

    def __init__(self, client) -> None:
        """
        Initialize the StateProxy instance.

        Args:
            client: The Client instance that this proxy is managing state for.
        """
        self.client = client
        self._state: Dict[str, Any] = {}

    def load(self) -> None:
        """
        Load the state data from the database using the configured user ID.

        If state data is loaded successfully, it's set to the local state and the client
        is notified that the state was loaded. Otherwise, logs an error message.
        """
        logging.info("<< Loading state")
        result = self.client.read_state(self.client.user_id)
        if result is not None:
            self._state = result
            self.client.state_was_loaded = True
        else:
            logging.error("Failed to load state.")

    def __getitem__(self, key: str) -> Any:
        """Get an item from the state by key."""
        return self._state[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item in the state."""
        self._state[key] = value

    def __delitem__(self, key: str) -> None:
        """Remove an item from the state by key if it exists."""
        if key in self._state:
            del self._state[key]

    def __str__(self) -> str:
        """Return the string representation of the state."""
        return str(self._state)

    def __repr__(self) -> str:
        """Return the official string representation of the StateProxy instance."""
        state_loaded = self.client.state_was_loaded
        return f"StateProxy(state={repr(self._state)}, state_was_loaded={state_loaded})"

    def items(self) -> Dict[str, Any].items:
        """Return a view of the state's items."""
        return self._state.items()

    def keys(self) -> Dict[str, Any].keys:
        """Return a view of the state's keys."""
        return self._state.keys()

    def values(self) -> Dict[str, Any].values:
        """Return a view of the state's values."""
        return self._state.values()

    def __iter__(self) -> Iterator[str]:
        """Return an iterator over the state's keys."""
        return iter(self._state)

    def __len__(self) -> int:
        """Return the number of items in the state."""
        return len(self._state)

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for key if key is in the state, else default."""
        return self._state.get(key, default)

    def save(self) -> None:
        """
        Save the state data to the database.

        If the state was loaded, the state is updated through the client using
        the configured user ID. If the state was not loaded, it logs a warning.
        """
        logging.info(">> Saving state")
        if not self.client.state_was_loaded:
            logging.warning("State was not loaded, skipping save.")
            return

        self.client.update_state(self.client.user_id, self._state)

# Eezo Client Library

The Eezo Client Library is a powerful, easy-to-use Python client for interacting with the Eezo API. Stay tuned for more features and improvements.

## Documentation

For the complete documentation of our project, please visit the following link:

[Eezo Documentation](https://eezo-ai.notion.site/Eezo-Documentation-2a598d6ff7274b668ac27021a35df4ef?pvs=74)

## Configuration

Before running the tests, you need to set up your environment with the necessary credentials.

1. Create a `.env` file in the root directory of the project with the following contents:

```env
EEZO_API_KEY=your_api_key
DEMO_AGENT_ID=your_agent_id
```

## Getting Started

To get up and running with the Eezo Client Library, follow these steps:

### Set up a Virtual Environment

Create a virtual environment to manage your project's dependencies:

```sh
python3 -m venv venv
```

Activate the virtual environment:

On macOS and Linux:

```sh
source venv/bin/activate
```

On Windows:

```cmd
.env\Scriptsctivate
```

### Install Dependencies

Install the required dependencies by running:

```sh
pip install -r requirements.txt
```

## Testing

Ensure everything is set up correctly by running the tests.

### Asynchronous Client

Run the asynchronous client tests with:

```sh
python test_async_client.py
```

### Synchronous Client

Run the synchronous client tests with:

```sh
python test_client.py
```

## Feedback

We welcome your feedback and contributions to the project. Please feel free to open an issue or create a pull request on our repository.

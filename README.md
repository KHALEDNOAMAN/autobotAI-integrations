# autobotAI-integrations

**autobotAI-Integrations** enables seamless connections between diverse workspaces, cloud AI platforms, and various tools to integrate with your code effortlessly. Currently, we support implementations in Python and Steampipe, boasting **25 integrations**, including major cloud providers such as AWS, GCP, and Azure. Additionally, we are continuously adding more integrations to expand our capabilities and better serve your needs.

## Installation

To install the `autobotAI-integrations` package, use the following command:

```sh
pip install git+https://github.com/shunyeka-spl/autobotAI-integrations
```

### Prerequisites

- **Python**: Ensure you have Python 3.11 or above installed on your system.
- **Steampipe**: To use the Steampipe integration, make sure Steampipe is installed on your system. You can download and install it from the [Steampipe official website](https://steampipe.io/downloads).

<!--## Usage

### Importing the Package

To start using `autobotAI-integrations`, you need to import the necessary modules in your code. Here's an example of how to import and use the package:

```python
from autobotAI_integrations.handlers import some_handler
from autobotAI_integrations.integrations import some_integration
from autobotAI_integrations.utils import some_utility

# Example usage
result = some_integration.connect()
print(result)
```

### Configuration

If your package requires any configuration (e.g., API keys, authentication details), provide details here on how to set it up. For example:

```python
import os

# Set up environment variables for authentication
os.environ['API_KEY'] = 'your_api_key'
os.environ['API_SECRET'] = 'your_api_secret'
```

### Code Examples

#### Example 1: Run payload file

```python
from autobotAI_integrations.handlers.payload_handler import handle_payload
from autobotAI_integrations.payload_schema import Payload
import json

payload_filename = "<payload_file_path>"

with open(payload_filename) as f:
    payload = json.load(f)

payload = Payload(**payload)


handle_payload(payload=payload, print_output=True)

```

## Features

- **Multiple Integrations**: Supports integration with various platforms and tools.
- **Python and Steampipe Support**: Initial support for Python and Steampipe.
- **Easy Configuration**: Simple setup and configuration for different integrations.

## Modules and Classes

### Handlers

- **`handlers.some_handler`**: Description of what this handler does.

### Integrations

- **`integrations.example_integration`**: Example integration with a specific service.
- **`integrations.steampipe_integration`**: Integration for Steampipe.

### Utilities

- **`utils.some_utility`**: Description of this utility function.
-->
## Testing

To run tests, you can use `pytest`. First, ensure you have `pytest` installed:

```sh
pip install pytest
```

Run the tests with:

```sh
pytest
```
<!--
### Test Configuration

If there are any specific configurations or environment setups needed for testing, provide the details here.

## Contributing

We welcome contributions from the community. To contribute:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

Please ensure your code adheres to our coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact Information

For support or inquiries, please contact us at:

- **Email**: support@shunyeka-spl.com
- **GitHub Issues**: [GitHub Issues Page](https://github.com/shunyeka-spl/autobotAI-integrations/issues)
-->
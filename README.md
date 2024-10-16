# AI-Bug-Bounty

An advanced, AI-powered tool for automated vulnerability scanning and bug bounty hunting.

## Overview

AI-Bug-Bounty combines cutting-edge machine learning techniques with traditional security tools to provide comprehensive security assessments. This project aims to automate the process of identifying vulnerabilities in web applications, making it an invaluable asset for both security professionals and bug bounty hunters.

## Key Features

- **AI-Driven Analysis**: Utilizes the Groq API for intelligent vulnerability detection and analysis.
- **Plugin Architecture**: Easily extendable with custom security scanning plugins.
- **Multi-Agent System**: Parallel scanning capabilities for improved performance.
- **Automated Reporting**: Generates detailed PDF reports of scan results with vulnerability charts.
- **Integration with Popular Tools**: Incorporates well-known security tools and techniques.
- **Web Interface**: User-friendly web UI for easy interaction and result visualization.
- **Vulnerability Database**: Integration with NVD for up-to-date vulnerability information.
- **Machine Learning Model**: Fine-tunable model for improved vulnerability detection.
- **Notification System**: Supports Telegram and Discord notifications for scan results.
- **Monitoring Mode**: Continuous scanning of target URLs at specified intervals.

## Prerequisites

- Python 3.9+
- Docker (optional)
- Groq API key
- Telegram Bot Token and Chat ID (optional)
- Discord Webhook URL (optional)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Likhithsai2580/AI-Bug-Bounty.git
   cd AI-Bug-Bounty
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your configuration:
   Create a `config.py` file in the root directory with the following content:

   ```python
   GROK_API_KEY = "YOUR_GROQ_API_KEY"
   TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
   TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
   DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"
   ```

   Replace the placeholder values with your actual API keys and IDs.

## Usage

1. Run the scanner:
   ```
   python main.py [TARGET_URLS] [--mode {regular,monitor}]
   ```
   Example:
   ```
   python main.py https://example.com https://test.com --mode monitor
   ```

2. For web interface (if implemented):
   ```
   python web_interface.py
   ```
   Then open your web browser and navigate to `http://localhost:5000`

3. View the results in the console output and check the generated PDF report in the `reports` directory.

## Configuration

### Plugin Configuration

Edit `plugin_config.yaml` to customize plugin behavior:

```
sql_injection:
  enabled: true
  options:
    timeout: 30
    max_depth: 3
```

### Adding New Plugins

1. Create a new Python file in the `plugins` directory (e.g., `my_plugin.py`)
2. Implement the plugin interface:

   ```python
   class Plugin:
       def __init__(self, options):
           self.options = options

       async def run(self, target_url):
           # Implement your scanning logic here
           return results

       def get_info(self):
           return {
               "name": "My Custom Plugin",
               "description": "Description of what the plugin does",
               "version": "1.0.0"
           }
   ```

3. Add the plugin configuration to `plugin_config.yaml`:

   ```yaml
   my_plugin:
     enabled: true
     options:
       custom_option: value
   ```

### Creating Plugin Documentation

To create documentation for your plugin, follow these steps:

1. Create a new Markdown file in the `docs/plugins` directory (e.g., `my_plugin.md`)
2. Document the plugin's functionality, configuration options, and usage examples.
3. Link the documentation file in the main `README.md` or a dedicated `docs/README.md` file.

## Project Structure

- `main.py`: Entry point of the application
- `agent_system.py`: Implements the multi-agent scanning system
- `plugin_manager.py`: Manages loading and running of plugins
- `llm/llama.py`: Wrapper for the Groq API integration
- `report_generator.py`: Generates PDF reports of scan results
- `plugins/`: Directory containing all scanning plugins
- `Dockerfile`: Defines the Docker image for the project

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and authorized testing purposes only. Always obtain permission before scanning any website you don't own or have explicit authorization to test.

## Support

If you find this project useful, consider supporting its development:

- GitHub: [Likhithsai2580](https://github.com/Likhithsai2580)
- Patreon: [anony45](https://www.patreon.com/anony45)

## Contact

For any queries or suggestions, please open an issue on the GitHub repository.

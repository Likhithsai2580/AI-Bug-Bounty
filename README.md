# AI-Bug-Bounty

An advanced, AI-powered tool for automated vulnerability scanning and bug bounty hunting.

## Overview

AI-Bug-Bounty combines cutting-edge machine learning techniques with traditional security tools to provide comprehensive security assessments. This project aims to automate the process of identifying vulnerabilities in web applications, making it an invaluable asset for both security professionals and bug bounty hunters.

## Key Features

- **AI-Driven Analysis**: Utilizes the Groq API for intelligent vulnerability detection and analysis.
- **Plugin Architecture**: Easily extendable with custom security scanning plugins.
- **Multi-Agent System**: Parallel scanning capabilities for improved performance.
- **Automated Reporting**: Generates detailed PDF reports of scan results.
- **Integration with Popular Tools**: Incorporates well-known security tools like nmap, sqlmap, and nikto.
- **Web Interface**: User-friendly web UI for easy interaction and result visualization.

## Prerequisites

- Docker
- Python 3.9+
- Groq API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/Likhithsai2580/AI-Bug-Bounty.git
   cd AI-Bug-Bounty
   ```

2. Set up your Groq API key:
   - Create a `config.py` file in the root directory
   - Add the following line, replacing `YOUR_API_KEY` with your actual Groq API key:
     ```python
     GROK_API_KEY = "YOUR_API_KEY"
     ```

3. Build the Docker image:
   ```
   docker build -t ai-bug-bounty .
   ```

## Usage

1. Run the scanner:
   ```
   docker run -it --rm -p 5000:5000 ai-bug-bounty
   ```

2. Open your web browser and navigate to `http://localhost:5000`

3. Enter the target URL in the web interface and start the scan

4. View the results in the web interface or check the generated PDF report in the `reports` directory

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

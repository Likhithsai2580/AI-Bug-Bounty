# AI-Bug-Bounty
A Development of AI to automate bug bounty

# Web Vulnerability Scanner

An advanced, AI-powered tool for automated vulnerability scanning of websites. This project combines machine learning techniques with traditional security tools to provide comprehensive security assessments.

## Features

- **AI-Driven Analysis**: Utilizes the Groq API for intelligent vulnerability detection and analysis.
- **Plugin Architecture**: Easily extendable with custom security scanning plugins.
- **Multi-Agent System**: Parallel scanning capabilities for improved performance.
- **Automated Reporting**: Generates detailed PDF reports of scan results.
- **Integration with Popular Tools**: Incorporates well-known security tools like nmap, sqlmap, and nikto.

## Prerequisites

- Docker
- Python 3.9+
- Groq API key

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/web-vulnerability-scanner.git
   cd web-vulnerability-scanner
   ```

2. Set up your Groq API key:
   - Open `config.py`
   - Replace `"sk-..."` with your actual Groq API key

3. Build the Docker image:
   ```
   docker build -t web-vuln-scanner .
   ```

## Usage

1. Run the scanner:
   ```
   docker run -it --rm web-vuln-scanner
   ```

2. Follow the prompts to enter the target URL and select scanning options.

3. Once the scan is complete, find the generated report in the `reports` directory.

## Configuration

### Plugin Configuration

Edit `plugin_config.yaml` to customize plugin behavior:

```yaml
sql_injection:
  enabled: true
  options:
    timeout: 30
    max_depth: 3
```

### Adding New Plugins

1. Create a new Python file in the `plugins` directory (e.g., `my_plugin.py`).
2. Implement the plugin interface:

   ```python
   class MyPlugin:
       def __init__(self, options):
           self.options = options

       def run(self, target_url):
           # Implement your scanning logic here
           return results
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

## License

[MIT License](LICENSE)

## Disclaimer

This tool is for educational and authorized testing purposes only. Always obtain permission before scanning any website you don't own.

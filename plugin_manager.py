import os
import importlib.util
import yaml
from typing import Dict, Any, List
import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

class PluginManager:
    def __init__(self, plugin_dir: str = "plugins", config_file: str = "plugin_config.yaml"):
        self.plugin_dir = plugin_dir
        self.config_file = config_file
        self.plugins = {}
        self.lock = asyncio.Lock()
        self._check_plugin_directory()

    def _check_plugin_directory(self):
        if not os.path.exists(self.plugin_dir):
            logger.warning(f"Plugin directory '{self.plugin_dir}' does not exist. Creating it.")
            os.makedirs(self.plugin_dir)

    async def initialize(self):
        await self.load_plugins()

    async def load_plugins(self):
        logger.info("Loading plugins...")
        config = self._load_config()
        logger.debug(f"Loaded plugin configuration: {config}")
        tasks = [self._load_plugin(plugin_name, plugin_config)
                 for plugin_name, plugin_config in config.items() if plugin_config.get('enabled', True)]
        logger.debug(f"Created {len(tasks)} tasks for plugin loading")
        await asyncio.gather(*tasks)

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return yaml.safe_load(f)
            except yaml.YAMLError as e:
                logger.error(f"Error parsing config file: {str(e)}")
                return {}
        else:
            logger.warning(f"Config file '{self.config_file}' not found. Using empty configuration.")
            return {}

    async def _load_plugin(self, plugin_name: str, plugin_config: Dict[str, Any]):
        try:
            plugin_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
            if not os.path.exists(plugin_path):
                if plugin_config.get('remote_url'):
                    await self._download_plugin(plugin_name, plugin_config['remote_url'])
                else:
                    raise ValueError(f"Plugin '{plugin_name}' not found and no remote URL provided")

            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "Plugin"):
                plugin_class = getattr(module, "Plugin")
                async with self.lock:
                    self.plugins[plugin_name] = plugin_class(plugin_config.get('options', {}))
                logger.info(f"Loaded plugin: {plugin_name}")
            else:
                raise ValueError(f"Plugin '{plugin_name}' does not have a Plugin class")
        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {str(e)}")

    async def _download_plugin(self, plugin_name: str, remote_url: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(remote_url) as response:
                    response.raise_for_status()
                    content = await response.text()
                    plugin_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
                    with open(plugin_path, 'w') as f:
                        f.write(content)
            logger.info(f"Downloaded plugin '{plugin_name}' from {remote_url}")
        except aiohttp.ClientError as e:
            raise ValueError(f"Failed to download plugin '{plugin_name}' from {remote_url}: {str(e)}")

    async def run_plugin(self, plugin_name: str, data: Dict[str, Any]) -> Any:
        async with self.lock:
            if plugin_name not in self.plugins:
                raise ValueError(f"Plugin '{plugin_name}' not found")
            plugin = self.plugins[plugin_name]
        try:
            return await plugin.run(data)
        except Exception as e:
            logger.error(f"Error running plugin '{plugin_name}': {str(e)}")
            return {"error": str(e)}

    async def run_all_plugins(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        tasks = [self.run_plugin(plugin_name, data) for plugin_name in self.plugins]
        return await asyncio.gather(*tasks)

    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        if plugin_name in self.plugins:
            return self.plugins[plugin_name].get_info()
        else:
            raise ValueError(f"Plugin '{plugin_name}' not found")

    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())

    async def reload_plugins(self):
        logger.info("Reloading plugins...")
        self.plugins.clear()
        await self.load_plugins()

class Plugin:
    def __init__(self, options):
        self.timeout = options.get('timeout', 60)
        self.max_depth = options.get('max_depth', 5)

    async def run(self, target_url):
        raise NotImplementedError("Plugin 'run' method must be implemented in subclasses")

    def get_info(self):
        return {
            "name": "Base Plugin",
            "description": "Base class for plugins",
            "version": "1.0.0"
        }
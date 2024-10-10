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
        logger.debug(f"Initializing PluginManager with plugin_dir={plugin_dir}, config_file={config_file}")
        self.plugin_dir = plugin_dir
        self.config_file = config_file
        self.plugins = {}
        self.lock = asyncio.Lock()
        self._check_plugin_directory()

    def _check_plugin_directory(self):
        logger.debug(f"Checking plugin directory: {self.plugin_dir}")
        if not os.path.exists(self.plugin_dir):
            logger.warning(f"Plugin directory '{self.plugin_dir}' does not exist. Creating it.")
            os.makedirs(self.plugin_dir)
        logger.debug(f"Plugin directory check complete")

    async def initialize(self):
        logger.debug("Initializing PluginManager")
        await self.load_plugins()
        logger.debug("PluginManager initialization complete")

    async def load_plugins(self):
        logger.info("Loading plugins...")
        config = self._load_config()
        logger.debug(f"Loaded plugin configuration: {config}")
        tasks = [self._load_plugin(plugin_name, plugin_config)
                 for plugin_name, plugin_config in config.items() if plugin_config.get('enabled', True)]
        logger.debug(f"Created {len(tasks)} tasks for plugin loading")
        await asyncio.gather(*tasks)
        logger.debug("All plugins loaded")

    def _load_config(self) -> Dict[str, Any]:
        logger.debug(f"Loading config from {self.config_file}")
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                logger.debug(f"Config loaded successfully: {config}")
                return config
            except yaml.YAMLError as e:
                logger.error(f"Error parsing config file: {str(e)}")
                return {}
        else:
            logger.warning(f"Config file '{self.config_file}' not found. Using empty configuration.")
            return {}

    async def _load_plugin(self, plugin_name: str, plugin_config: Dict[str, Any]):
        logger.debug(f"Loading plugin: {plugin_name}")
        try:
            plugin_path = os.path.join(self.plugin_dir, f"{plugin_name}.py")
            if not os.path.exists(plugin_path):
                logger.debug(f"Plugin file not found: {plugin_path}")
                if plugin_config.get('remote_url'):
                    await self._download_plugin(plugin_name, plugin_config['remote_url'])
                else:
                    raise ValueError(f"Plugin '{plugin_name}' not found and no remote URL provided")

            logger.debug(f"Importing plugin: {plugin_name}")
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "Plugin"):
                plugin_class = getattr(module, "Plugin")
                logger.debug(f"Instantiating plugin: {plugin_name}")
                async with self.lock:
                    self.plugins[plugin_name] = plugin_class(plugin_config.get('options', {}))
                logger.info(f"Loaded plugin: {plugin_name}")
            else:
                raise ValueError(f"Plugin '{plugin_name}' does not have a Plugin class")
        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {str(e)}")

    async def _download_plugin(self, plugin_name: str, remote_url: str):
        logger.debug(f"Downloading plugin '{plugin_name}' from {remote_url}")
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
        logger.debug(f"Running plugin: {plugin_name}")
        async with self.lock:
            if plugin_name not in self.plugins:
                raise ValueError(f"Plugin '{plugin_name}' not found")
            plugin = self.plugins[plugin_name]
        try:
            result = await plugin.run(data)
            logger.debug(f"Plugin '{plugin_name}' execution complete")
            return result
        except Exception as e:
            logger.error(f"Error running plugin '{plugin_name}': {str(e)}")
            return {"error": str(e)}

    async def run_all_plugins(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.debug("Running all plugins")
        tasks = [self.run_plugin(plugin_name, data) for plugin_name in self.plugins]
        results = await asyncio.gather(*tasks)
        logger.debug("All plugins execution complete")
        return results

    def get_plugin_info(self, plugin_name: str) -> Dict[str, Any]:
        logger.debug(f"Getting info for plugin: {plugin_name}")
        if plugin_name in self.plugins:
            info = self.plugins[plugin_name].get_info()
            logger.debug(f"Plugin info: {info}")
            return info
        else:
            raise ValueError(f"Plugin '{plugin_name}' not found")

    def list_plugins(self) -> List[str]:
        logger.debug("Listing all plugins")
        plugin_list = list(self.plugins.keys())
        logger.debug(f"Plugin list: {plugin_list}")
        return plugin_list

    async def reload_plugins(self):
        logger.info("Reloading plugins...")
        self.plugins.clear()
        await self.load_plugins()
        logger.debug("Plugins reloaded")

class Plugin:
    def __init__(self, options):
        logger.debug(f"Initializing Plugin with options: {options}")
        self.timeout = options.get('timeout', 60)
        self.max_depth = options.get('max_depth', 5)

    async def run(self, target_url):
        logger.debug(f"Running plugin with target_url: {target_url}")
        raise NotImplementedError("Plugin 'run' method must be implemented in subclasses")

    def get_info(self):
        logger.debug("Getting plugin info")
        info = {
            "name": "Base Plugin",
            "description": "Base class for plugins",
            "version": "1.0.0"
        }
        logger.debug(f"Plugin info: {info}")
        return info
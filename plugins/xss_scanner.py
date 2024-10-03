import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)

class Plugin:
    def __init__(self, options):
        self.timeout = options.get('timeout', 30)
        self.max_depth = options.get('max_depth', 3)
        self.payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')"
        ]

    async def run(self, data):
        url = data.get('url')
        if not url:
            logger.error("No URL provided for XSS scan")
            return {"error": "No URL provided"}

        logger.info(f"Starting XSS scan for {url}")
        results = []
        visited = set()
        await self._scan_url(url, 0, visited, results)
        logger.info(f"XSS scan completed for {url}")
        return {"vulnerable_points": results}

    async def _scan_url(self, url, depth, visited, results):
        if depth > self.max_depth or url in visited:
            return

        visited.add(url)
        logger.debug(f"Scanning URL: {url} (depth: {depth})")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')

                    form_results = await self._check_forms(url, soup)
                    results.extend(form_results)

                    param_result = await self._check_get_params(url)
                    if param_result:
                        results.append(param_result)

            if depth < self.max_depth:
                links = soup.find_all('a', href=True)
                tasks = [self._scan_url(urljoin(url, link['href']), depth + 1, visited, results)
                         for link in links if urljoin(url, link['href']).startswith(url)]
                await asyncio.gather(*tasks)

        except aiohttp.ClientError as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            results.append({"error": f"Request failed for {url}: {str(e)}"})

    async def _check_forms(self, url, soup):
        results = []
        forms = soup.find_all('form')
        for form in forms:
            result = await self._check_form(url, form)
            if result:
                results.append(result)
        return results

    async def _check_form(self, url, form):
        action = urljoin(url, form.get('action', ''))
        method = form.get('method', 'get').lower()
        inputs = form.find_all('input')

        for input_field in inputs:
            if input_field.get('type') in ['text', 'search', 'url', 'tel']:
                for payload in self.payloads:
                    data = {input_field['name']: payload}
                    try:
                        async with aiohttp.ClientSession() as session:
                            if method == 'post':
                                async with session.post(action, data=data, timeout=self.timeout) as response:
                                    content = await response.text()
                            else:
                                async with session.get(action, params=data, timeout=self.timeout) as response:
                                    content = await response.text()
                        
                        if self._check_xss_reflection(content, payload):
                            return {
                                "url": url,
                                "form_action": action,
                                "form_method": method,
                                "vulnerable_input": input_field['name'],
                                "payload": payload,
                                "reason": "XSS payload reflected in response"
                            }
                    except aiohttp.ClientError as e:
                        logger.error(f"Request failed for {action}: {str(e)}")
                        continue

        return None

    async def _check_get_params(self, url):
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)
        
        for param_name, param_value in params.items():
            for payload in self.payloads:
                test_url = url.replace(f"{param_name}={param_value[0]}", f"{param_name}={payload}")
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(test_url, timeout=self.timeout) as response:
                            content = await response.text()
                    if self._check_xss_reflection(content, payload):
                        return {
                            "url": url,
                            "vulnerable_param": param_name,
                            "payload": payload,
                            "reason": "XSS payload reflected in response"
                        }
                except aiohttp.ClientError as e:
                    logger.error(f"Request failed for {test_url}: {str(e)}")
                    continue

        return None

    def _check_xss_reflection(self, content, payload):
        return payload in content

    def get_info(self):
        return {
            "name": "XSS Scanner",
            "description": "Scans for Cross-Site Scripting (XSS) vulnerabilities",
            "version": "1.0.0"
        }
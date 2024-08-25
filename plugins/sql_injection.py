import requests
from bs4 import BeautifulSoup

class Plugin:
    def __init__(self, options):
        self.timeout = options.get('timeout', 30)
        self.max_depth = options.get('max_depth', 3)

    def run(self, data):
        url = data.get('url')
        if not url:
            return {"error": "No URL provided"}

        try:
            response = requests.get(url, timeout=self.timeout)
            soup = BeautifulSoup(response.text, 'html.parser')
            forms = soup.find_all('form')

            results = []
            for form in forms:
                result = self.check_form(form)
                if result:
                    results.append(result)

            return {"vulnerable_forms": results}
        except requests.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}

    def check_form(self, form):
        action = form.get('action', '')
        method = form.get('method', 'get').lower()
        inputs = form.find_all('input')

        for input_field in inputs:
            if input_field.get('type') == 'text':
                # Here you would implement actual SQL injection checks
                # This is a simplified example
                return {
                    "form_action": action,
                    "form_method": method,
                    "vulnerable_input": input_field.get('name'),
                    "reason": "Potential SQL injection point found"
                }

        return None

    def get_info(self):
        return {
            "name": "SQL Injection Scanner",
            "description": "Scans for potential SQL injection vulnerabilities in forms",
            "version": "1.0.0"
        }
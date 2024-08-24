from groq import Groq
import time
from config import GROK_API_KEY
import logging
import threading

logger = logging.getLogger(__name__)

class LLM:
    def __init__(self):
        self.client = Groq(api_key=GROK_API_KEY)
        self.messages = [
            {"role": "system", "content": """You are an AI assistant tasked with analyzing websites for vulnerabilities. 
            You have full terminal access and can execute multiple commands. You can use system commands, Python code, or a combination of both.
            Examples of what you can do:
            - Install packages: apt-get update && apt-get install -y <package-name>
            - Run security tools: nmap, sqlmap, nikto, etc.
            - Execute shell commands: ls, cat, grep, sed, awk
            - Use network tools: curl, wget, netcat
            - Run Python scripts or use Python libraries
            
            When providing code, you can use os.system(), subprocess.run(), or any Python functions to execute commands and process results.
            Always consider the security implications of the commands you suggest and provide explanations for your actions."""}
        ]
        self.lock = threading.Lock()

    def generate(self, prompt, model="llama3-70b-8192", max_retries=3, retry_delay=5):
        with self.lock:
            self.messages.append({"role": "user", "content": prompt})

            for attempt in range(max_retries):
                try:
                    chat_completion = self.client.chat.completions.create(
                        messages=self.messages,
                        model=model
                    )
                    response = chat_completion.choices[0].message.content
                    self.messages.append({"role": "assistant", "content": response})
                    return response
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        logger.error("Max retries reached. Returning None.")
                        return None
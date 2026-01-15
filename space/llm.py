import ollama
from typing import List, Dict, Any, Generator

class ChatModel:
    def __init__(self, model: str = "llama3"):
        self.model = model

    def generate(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Any:
        """
        Generate a response from the model.
        """
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                tools=tools,
                think=True,
            )
            return response
        except Exception as e:
            return {"error": str(e)}

    def generate_stream(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Generator:
        """
        Generate a streaming response from the model.
        """
        try:
            stream = ollama.chat(
                model=self.model,
                messages=messages,
                tools=tools,
                stream=True,
                think=True,
            )
            for chunk in stream:
                yield chunk
        except Exception as e:
            yield {"error": str(e)}

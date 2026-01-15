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
            try:
                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    think=True,
                    stream=True,
                )
                return response
            except ollama.ResponseError as e:
                # Fallback if model doesn't support thinking
                if e.status_code == 400 and "does not support thinking" in str(e):
                    response = ollama.chat(
                        model=self.model,
                        messages=messages,
                        tools=tools,
                        stream=True,
                    )
                    return response
                raise e
        except Exception as e:
            return {"error": str(e)}

    def generate_stream(self, messages: List[Dict[str, str]], tools: List[Dict[str, Any]] = None) -> Generator:
        """
        Generate a streaming response from the model.
        """
        try:
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
            except ollama.ResponseError as e:
                # Fallback if model doesn't support thinking
                if e.status_code == 400 and "does not support thinking" in str(e):
                    stream = ollama.chat(
                        model=self.model,
                        messages=messages,
                        tools=tools,
                        stream=True,
                    )
                    for chunk in stream:
                        yield chunk
                else:
                    raise e
        except Exception as e:
            yield {"error": str(e)}

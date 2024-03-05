from litellm import completion

class Agent():
    def __init__(self, name, model_type, key):
        self.name = name
        self.model_type = model_type
        self.key = key

        possible_models = [
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo",
            "gpt4-1106-preview"
        ]

        if self.model_type not in possible_models:
            raise Exception("Model Input not valid")

    def modelType(self):
        return self.model_type
    
    def query(self, message):
        response = completion(
            api_key = self.key,
            base_url = "https://drchat.xyz",
            model = self.model_type,
            custom_llm_provider="openai",
            messages = [{ "content": message,"role": "user"}]
        )
        return response
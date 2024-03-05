class prompt():
    def __init__(self, definitions, domain, message):
        self.definitions = definitions
        self.domain = domain
        self.message = message

    def get_definitions(self):
        return self.definitions

    def get_domain(self):
        return self.domain
    
    def get_message(self):
        return self.message
    
    def get_initial_prompt(self):
        initial_prompt = f"""
        Key Definitions:

        """
        return initial_prompt


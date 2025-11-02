import os
from dotenv import load_dotenv
from google import genai
from .guardrails import InputValidator, APIGuardrails, rate_limit

load_dotenv()

class Chatbot:
    def __init__(self):
        """Initialize the Gemini API client"""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in .env file")
            
            # Set the API key as environment variable for the new SDK
            os.environ["GEMINI_API_KEY"] = api_key
            
            # Initialize the client - the new way
            self.client = genai.Client()
            
        except Exception as e:
            print(f"Error configuring Gemini API: {e}")
            self.client = None

    @rate_limit(max_requests=50, time_window=60)
    def get_general_response(self, user_prompt, chat_history):
        """Get a general response from the AI model"""
        if not self.client:
            return "Error: Gemini API is not configured. Please check your API key."
        
        # Validate input
        is_valid, error = InputValidator.validate_text_input(user_prompt, max_length=10000)
        if not is_valid:
            return f"Error: Invalid input - {error}"
            
        # Build the conversation context
        full_prompt = "You are a helpful legal assistant chatbot.\n"
        for message in chat_history:
            role = "User" if message['role'] == 'user' else "Assistant"
            full_prompt += f"{role}: {message['content']}\n"
        full_prompt += f"User: {user_prompt}\nAssistant:"
        
        # Check token limit
        is_within_limit, limit_msg = APIGuardrails.check_token_limit(full_prompt)
        if not is_within_limit:
            return f"Error: {limit_msg}"

        try:
            # Use the new SDK method
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            return f"Error: Unable to get response from AI. {str(e)}"

    @rate_limit(max_requests=50, time_window=60)
    def get_document_context_response(self, user_prompt, document_text, chat_history):
        """Get a response based on document context"""
        if not self.client:
            return "Error: Gemini API is not configured. Please check your API key."
        
        # Validate inputs
        is_valid, error = InputValidator.validate_text_input(user_prompt, max_length=10000)
        if not is_valid:
            return f"Error: Invalid prompt - {error}"
        
        is_valid, error = InputValidator.validate_text_input(document_text, max_length=1000000)
        if not is_valid:
            return f"Error: Invalid document - {error}"
        
        # Sanitize user prompt
        user_prompt = InputValidator.sanitize_text(user_prompt)

        # Build the system prompt with document context
        system_prompt = f"""
            You are a specialized legal assistant. Your task is to answer questions based on the provided legal document.
            Do not answer any questions that are not related to the document.
            If the answer is not in the document, state that clearly.

            Here is the document content:
            ---
            {document_text}
            ---
            """
        
        # Build the full conversation context
        full_prompt = system_prompt
        for message in chat_history:
            role = "User" if message['role'] == 'user' else "Assistant"
            full_prompt += f"{role}: {message['content']}\n"
        full_prompt += f"User: {user_prompt}\nAssistant:"
        
        # Check token limit
        is_within_limit, limit_msg = APIGuardrails.check_token_limit(full_prompt)
        if not is_within_limit:
            return f"Error: {limit_msg}"

        try:
            # Use the new SDK method
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=full_prompt
            )
            return response.text
        except Exception as e:
            return f"Error: Unable to get response from AI. {str(e)}"
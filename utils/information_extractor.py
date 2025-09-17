import os
import google.generativeai as genai
import json
import re

class InformationExtractor:
    """
    Extracts structured key-value data from contract text using a highly specific
    prompt for the Gemini 1.5 Flash model.
    """
    def __init__(self):
        """Initializes the InformationExtractor and configures the Gemini model."""
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not found.")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini model: {e}")

    def extract_entities(self, full_text):
        """
        Analyzes the full text of a contract and extracts a predefined set of key entities.

        Args:
            full_text (str): The complete text of the contract.

        Returns:
            dict: A dictionary containing the extracted entities. Returns default
                    "Not Found" values upon failure.
        """
        # This is the dictionary structure we expect.
        default_entities = {
            "governing_law": "Not Found",
            "termination_notice_period_days": "Not Found",
            "liability_cap_amount": "Not Found",
            "late_fee_percentage": "Not Found"
        }

        # --- THE NEW, BULLETPROOF PROMPT ---
        prompt = f"""
        You are a highly-trained paralegal AI specializing in contract data extraction.
        Your task is to analyze the following contract text and extract specific key information.

        **Instructions:**
        1.  Read the entire contract text carefully.
        2.  Extract the values for the following keys:
            - `governing_law`: The state or country whose laws govern the contract (e.g., "State of California").
            - `termination_notice_period_days`: The notice period required for termination, in days. Extract numbers only.
            - `liability_cap_amount`: The maximum liability amount. Extract the value (e.g., "the total fees paid... in the one (1) month preceding").
            - `late_fee_percentage`: The late fee as a percentage. Extract numbers only.
        3.  You MUST respond with a single, clean JSON object.
        4.  The keys in your JSON object must be exactly: "governing_law", "termination_notice_period_days", "liability_cap_amount", "late_fee_percentage".
        5.  **CRITICAL:** If you cannot find a value for a specific key, the value for that key in the JSON object MUST be `null`. Do not omit the key.

        **Contract Text to Analyze:**
        ---
        {full_text}
        ---

        **Your JSON Response:**
        """

        try:
            print("📊 Starting information extraction...")
            response = self.model.generate_content(prompt)
            
            # Use regex to find the JSON block, making it robust to extra text
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if not json_match:
                print(f"⚠️ IER Error: No valid JSON object found in the model's response.")
                print(f"Raw Response: {response.text}")
                return default_entities
            
            extracted_json_str = json_match.group(0)
            extracted_entities = json.loads(extracted_json_str)
            print(f"✅ IER Success: Extracted entities: {extracted_entities}")

            # Merge the extracted entities with the defaults to ensure all keys exist
            # and replace any `null` values with "Not Found" for display.
            final_entities = default_entities.copy()
            for key, value in extracted_entities.items():
                if key in final_entities and value is not None:
                    final_entities[key] = value
            
            return final_entities

        except (json.JSONDecodeError, Exception) as e:
            print(f"❌ IER Critical Error: Failed to parse or process Gemini response for entities: {e}")
            if 'response' in locals():
                print(f"Raw Response that caused error: {response.text}")
            return default_entities


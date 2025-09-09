import google.cloud.dlp_v2
from google.api_core.exceptions import GoogleAPICallError

class PrivacyProcessor:
    def __init__(self, project_id):
        self.project_id = project_id
        self.dlp_client = google.cloud.dlp_v2.DlpServiceClient()

    def redact_text(self, text_to_redact):
        """
        Uses the Data Loss Prevention API to redact sensitive information from a
        string.
        """
        if not self.project_id:
            raise ValueError("Google Cloud project ID is not set.")

        parent = f"projects/{self.project_id}"

        # Construct the item to inspect
        item = {"value": text_to_redact}

        # The info types to search for in the text
        info_types = [
            {"name": "PERSON_NAME"},
            {"name": "PHONE_NUMBER"},
            {"name": "EMAIL_ADDRESS"},
            {"name": "US_SOCIAL_SECURITY_NUMBER"},
            {"name": "CREDIT_CARD_NUMBER"},
        ]

        # The configuration for the inspect request
        inspect_config = {
            "info_types": info_types,
            "min_likelihood": "LIKELY",
            "include_quote": True,
        }

        # The configuration for the redact request
        redact_config = {
            "replace_with_info_type": True,
        }

        # Construct the request
        request = {
            "parent": parent,
            "inspect_config": inspect_config,
            "item": item,
            "deidentify_config": {
                "info_type_transformations": {
                    "transformations": [
                        {
                            "primitive_transformation": {
                                "replace_with_info_type_config": {}
                            }
                        }
                    ]
                }
            },
        }

        try:
            # Call the API
            response = self.dlp_client.deidentify_content(request=request)
            return response.item.value
        except GoogleAPICallError as e:
            print(f"Error calling DLP API: {e}")
            return f"Error during redaction: {e}"
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return f"An unexpected error occurred during redaction: {e}"

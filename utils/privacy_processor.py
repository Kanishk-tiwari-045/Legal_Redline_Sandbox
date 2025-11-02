import google.cloud.dlp_v2
from google.api_core.exceptions import GoogleAPICallError
import numpy as np
from cryptography.fernet import Fernet
import base64
import os

class PrivacyProcessor:
    def __init__(self, project_id, dp_sigma=0.2):
        """
        Initialize Privacy Processor with:
        - project_id: GCP Project ID
        - dp_sigma: standard deviation for Gaussian noise (lower = less deviation)
        """
        self.project_id = project_id
        self.dlp_client = google.cloud.dlp_v2.DlpServiceClient()
        self.dp_sigma = dp_sigma  # controls privacy/utility tradeoff

        # AES key generation (or load from environment variable)
        key_env = os.getenv("AES_KEY")
        if key_env:
            self.aes_key = key_env.encode()
        else:
            self.aes_key = Fernet.generate_key()
            print("[WARN] AES_KEY not found in env. Generated temporary key.")
        self.cipher = Fernet(self.aes_key)

    # ------------------------------------------
    # 1️⃣ Differential Privacy (Gaussian Noise)
    # ------------------------------------------
    def _apply_gaussian_noise(self, value):
        """Add small Gaussian noise to numeric values."""
        try:
            numeric_value = float(value)
            noise = np.random.normal(0, self.dp_sigma)
            return str(numeric_value + noise)
        except ValueError:
            # Not numeric, skip DP
            return value

    # ------------------------------------------
    # 2️⃣ AES Encryption & Decryption
    # ------------------------------------------
    def encrypt_text(self, text):
        """Encrypt text using AES (Fernet) encryption."""
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt_text(self, encrypted_text):
        """Decrypt AES-encrypted text."""
        return self.cipher.decrypt(encrypted_text.encode()).decode()

    # ------------------------------------------
    # 3️⃣ DLP Redaction + Pseudonymization
    # ------------------------------------------
    def redact_and_pseudonymize(self, text_to_redact):
        """
        Uses the Data Loss Prevention API to redact sensitive information
        and replace it with pseudonymous info type tags.
        """
        if not self.project_id:
            raise ValueError("Google Cloud project ID is not set.")

        parent = f"projects/{self.project_id}"

        item = {"value": text_to_redact}
        info_types = [
            {"name": "PERSON_NAME"},
            {"name": "PHONE_NUMBER"},
            {"name": "EMAIL_ADDRESS"},
            {"name": "US_SOCIAL_SECURITY_NUMBER"},
            {"name": "CREDIT_CARD_NUMBER"},
        ]

        inspect_config = {
            "info_types": info_types,
            "min_likelihood": "LIKELY",
            "include_quote": True,
        }

        # Pseudonymization transformation
        deidentify_config = {
            "info_type_transformations": {
                "transformations": [
                    {
                        "primitive_transformation": {
                            "replace_with_info_type_config": {}
                        }
                    }
                ]
            }
        }

        request = {
            "parent": parent,
            "inspect_config": inspect_config,
            "item": item,
            "deidentify_config": deidentify_config,
        }

        try:
            response = self.dlp_client.deidentify_content(request=request)
            pseudonymized_text = response.item.value
            return pseudonymized_text
        except GoogleAPICallError as e:
            print(f"[ERROR] DLP API call failed: {e}")
            return f"Error during redaction: {e}"
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return f"Unexpected error: {e}"

    # ------------------------------------------
    # 4️⃣ Combined Secure Processing Pipeline
    # ------------------------------------------
    def process_text_securely(self, text):
        """
        Complete privacy-preserving pipeline:
        1. Redact & pseudonymize sensitive info
        2. Add small Gaussian noise to numeric data
        3. Encrypt the final output
        """
        redacted_text = self.redact_and_pseudonymize(text)

        # Apply DP only on numeric substrings
        words = redacted_text.split()
        noisy_words = [self._apply_gaussian_noise(w) for w in words]
        dp_text = " ".join(noisy_words)

        encrypted_text = self.encrypt_text(dp_text)
        return encrypted_text

    # ------------------------------------------
    # 5️⃣ Utility to Decrypt and Inspect
    # ------------------------------------------
    def decrypt_and_show(self, encrypted_text):
        """For debugging: decrypts text for verification."""
        try:
            return self.decrypt_text(encrypted_text)
        except Exception:
            return "[Decryption Failed or Unauthorized]"

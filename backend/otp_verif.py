import os
import logging
from typing import Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
from fastapi import HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

__all__ = ['OTPRequest', 'OTPVerifyRequest', 'OTPService', 'otp_service']

class OTPRequest(BaseModel):
    email: str

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class OTPService:
    def __init__(self):
        self.otp_store: Dict[str, str] = {}
        self.sender_email = os.getenv('EMAIL_USER')
        self.sender_password = os.getenv('EMAIL_PASSWORD')

        if not self.sender_email or not self.sender_password:
            logger.warning("Email credentials not configured")

    async def generate_and_send_otp(self, request: OTPRequest):
        """Generate and send OTP to user's email"""
        if not self.sender_email or not self.sender_password:
            raise HTTPException(
                status_code=500, 
                detail="Email service not configured"
            )

        # Generate 6-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.otp_store[request.email] = otp

        try:
            message = MIMEMultipart()
            message["From"] = self.sender_email
            message["To"] = request.email
            message["Subject"] = "Your Legal AI Verification Code"

            body = f"""
            Your verification code is: {otp}
            
            This code will expire in 5 minutes.
            If you didn't request this code, please ignore this email.
            """
            message.attach(MIMEText(body, "plain"))

            # Create SMTP session
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)

            logger.info(f"OTP sent successfully to {request.email}")
            return {"message": "OTP sent successfully"}

        except Exception as e:
            logger.error(f"Failed to send OTP: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send OTP: {str(e)}"
            )

    async def verify_otp(self, request: OTPVerifyRequest):
        """Verify the OTP entered by user"""
        stored_otp = self.otp_store.get(request.email)
        
        if not stored_otp:
            raise HTTPException(
                status_code=400,
                detail="OTP expired or not found"
            )

        if request.otp != stored_otp:
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP"
            )

        # Clear OTP after successful verification
        del self.otp_store[request.email]
        logger.info(f"OTP verified successfully for {request.email}")
        
        return {"message": "OTP verified successfully"}

# Create a singleton instance
otp_service = OTPService()
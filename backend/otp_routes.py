from fastapi import APIRouter
from otp_verif import otp_service, OTPRequest, OTPVerifyRequest

router = APIRouter()

@router.post("/send-otp")
async def send_otp(request: OTPRequest):
    """Send OTP to user's email"""
    return await otp_service.generate_and_send_otp(request)

@router.post("/verify-otp")
async def verify_otp(request: OTPVerifyRequest):
    """Verify OTP entered by user"""
    return await otp_service.verify_otp(request)
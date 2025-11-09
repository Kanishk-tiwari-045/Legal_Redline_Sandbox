import express from "express";
import cors from "cors";
import nodemailer from "nodemailer";
import crypto from "crypto";
import dotenv from "dotenv";
import fs from "fs";
import path from "path";
import jwt from "jsonwebtoken";

// Load .env: prefer local auth-server/.env, fall back to repository root ../.env
(() => {
  const localEnv = path.resolve(process.cwd(), '.env');
  const parentEnv = path.resolve(process.cwd(), '..', '.env');

  if (fs.existsSync(localEnv)) {
    dotenv.config({ path: localEnv });
    console.log(`🔐 Loaded environment from ${localEnv}`);
  } else if (fs.existsSync(parentEnv)) {
    dotenv.config({ path: parentEnv });
    console.log(`🔐 Loaded environment from ${parentEnv}`);
  } else {
    // Last resort: attempt default lookup (process.cwd())
    dotenv.config();
    console.log('⚠️  No .env found in auth-server or parent directory; dotenv attempted default load.');
  }
})();

const app = express();
app.use(cors({
  origin: ['https://legal-redline-sandbox-nine.vercel.app', 'http://localhost:5173', 'http://localhost:3000'], // Allow Vite dev server
  credentials: true
}));
app.use(express.json());

// In-memory stores (use Redis in production)
const otpStore = {};
const sessionStore = {};

// Email transporter
const transporter = nodemailer.createTransport({
  service: "gmail",
  auth: {
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASSWORD,
  },
});

// Middleware to verify JWT
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers["authorization"];
  const token = authHeader && authHeader.split(" ")[1];

  if (!token) {
    return res.status(401).json({ error: "Access token required" });
  }

  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(403).json({ error: "Invalid or expired token" });
    }
    req.user = user;
    next();
  });
};

// Generate JWT token
const generateToken = (email, sessionId) => {
  return jwt.sign(
    { email, sessionId },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRES_IN || "24h" }
  );
};

// Route: Register User (for anonymous/guest users)
app.post("/auth/register", async (req, res) => {
  const { email, username, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ error: "Email and password are required" });
  }

  // For anonymous users, just return success
  res.json({ 
    success: true, 
    message: "Anonymous user registered successfully",
    userId: crypto.randomUUID()
  });
});

// Route: Login User
app.post("/auth/login", async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ error: "Email and password are required" });
  }

  // For anonymous users, create a session and return token
  const sessionId = crypto.randomUUID();
  const token = generateToken(email, sessionId);
  
  // Store session
  sessionStore[sessionId] = {
    email,
    createdAt: Date.now(),
    lastActive: Date.now()
  };

  res.json({
    access_token: token,
    token_type: "bearer",
    expires_in: 86400,
    user: { email, id: sessionId }
  });
});

// Route: Send OTP
app.post("/auth/send-otp", async (req, res) => {
  const { email } = req.body;

  if (!email) {
    return res.status(400).json({ error: "Email is required" });
  }

  // Basic email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return res.status(400).json({ error: "Invalid email format" });
  }

  const otp = crypto.randomInt(100000, 999999).toString();
  otpStore[email] = {
    otp,
    expiresAt: Date.now() + 5 * 60 * 1000, // 5 minutes
    attempts: 0
  };

  try {
    await transporter.sendMail({
      from: `Legal AI <${process.env.EMAIL_USER}>`,
      to: email,
      subject: "Your Legal AI OTP Code",
      html: `
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #1f2937; border-radius: 10px;">
          <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #3b82f6; margin: 0; font-size: 28px;">⚖️ Legal AI</h1>
          </div>
          
          <div style="background-color: #374151; border-radius: 8px; padding: 30px; text-align: center;">
            <h2 style="color: #e5e7eb; margin-top: 0;">Your Verification Code</h2>
            <p style="color: #9ca3af; font-size: 14px; margin-bottom: 20px;">
              Enter this code to access your Legal AI session
            </p>
            
            <div style="background-color: #1f2937; border: 2px solid #3b82f6; border-radius: 8px; padding: 20px; margin: 20px 0;">
              <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #3b82f6; font-family: monospace;">
                ${otp}
              </span>
            </div>
            
            <p style="color: #9ca3af; font-size: 12px; margin-top: 20px;">
              This code expires in <strong style="color: #ef4444;">5 minutes</strong>
            </p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #4b5563;">
              <p style="color: #6b7280; font-size: 11px; margin: 5px 0;">
                If you didn't request this code, please ignore this email.
              </p>
              <p style="color: #6b7280; font-size: 11px; margin: 5px 0;">
                For security reasons, never share this code with anyone.
              </p>
            </div>
          </div>
          
          <div style="text-align: center; margin-top: 20px;">
            <p style="color: #6b7280; font-size: 12px;">
              © ${new Date().getFullYear()} Legal AI. All rights reserved.
            </p>
          </div>
        </div>
      `,
    });

    console.log(`OTP sent to ${email}: ${otp}`);
    res.json({ 
      message: "OTP sent successfully!",
      expiresIn: 300 // seconds
    });
  } catch (err) {
    console.error("Email send error:", err);
    res.status(500).json({ error: "Failed to send OTP. Please try again." });
  }
});

// Route: Verify OTP and return JWT
app.post("/auth/verify-otp", (req, res) => {
  const { email, otp } = req.body;

  if (!email || !otp) {
    return res.status(400).json({ error: "Email and OTP are required" });
  }

  const storedOtp = otpStore[email];

  if (!storedOtp) {
    return res.status(400).json({ error: "No OTP found. Please request a new one." });
  }

  // Check attempts
  if (storedOtp.attempts >= 3) {
    delete otpStore[email];
    return res.status(429).json({ error: "Too many failed attempts. Please request a new OTP." });
  }

  // Check if OTP expired
  if (Date.now() > storedOtp.expiresAt) {
    delete otpStore[email];
    return res.status(400).json({ error: "OTP has expired. Please request a new one." });
  }

  // Verify OTP
  if (storedOtp.otp !== otp) {
    storedOtp.attempts++;
    return res.status(400).json({ 
      error: `Invalid OTP. ${3 - storedOtp.attempts} attempts remaining.` 
    });
  }

  // OTP verified successfully
  delete otpStore[email];

  // Create session
  const sessionId = crypto.randomBytes(32).toString('hex');
  const token = generateToken(email, sessionId);

  sessionStore[sessionId] = {
    email,
    createdAt: new Date().toISOString(),
    lastActivity: new Date().toISOString()
  };

  res.json({
    message: "OTP verified successfully!",
    token,
    user: { email },
    sessionId
  });
});

// Route: Verify Token (for checking if token is still valid)
app.get("/auth/verify-token", authenticateToken, (req, res) => {
  const session = sessionStore[req.user.sessionId];
  
  if (!session) {
    return res.status(401).json({ error: "Session not found" });
  }

  // Update last activity
  session.lastActivity = new Date().toISOString();

  res.json({
    valid: true,
    user: { email: req.user.email },
    sessionId: req.user.sessionId
  });
});

// Route: Logout
app.post("/auth/logout", authenticateToken, (req, res) => {
  // Remove session
  delete sessionStore[req.user.sessionId];
  
  res.json({ message: "Logged out successfully" });
});

// Route: Refresh Token
app.post("/auth/refresh-token", authenticateToken, (req, res) => {
  const session = sessionStore[req.user.sessionId];
  
  if (!session) {
    return res.status(401).json({ error: "Session not found" });
  }

  // Generate new token
  const newToken = generateToken(req.user.email, req.user.sessionId);
  session.lastActivity = new Date().toISOString();

  res.json({
    message: "Token refreshed",
    token: newToken
  });
});

// Health check
app.get("/auth/health", (req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

// Cleanup expired OTPs every 5 minutes
setInterval(() => {
  const now = Date.now();
  Object.keys(otpStore).forEach(email => {
    if (otpStore[email].expiresAt < now) {
      delete otpStore[email];
    }
  });
}, 5 * 60 * 1000);

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`✅ Auth Server running on http://localhost:${PORT}`);
  console.log(`📧 Email configured: ${process.env.EMAIL_USER}`);
});
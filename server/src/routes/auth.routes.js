import { Router } from 'express';
import rateLimit from 'express-rate-limit';
import { User } from '../models/User.js';
import { db } from '../config/db.js';
import { signAuthToken, generateResetToken, hashResetToken } from '../utils/token.js';
import { authenticate } from '../middleware/auth.js';
import { validateRegister, validateLogin, validateEmail, validatePassword } from '../middleware/validate.js';

const router = Router();

// Slow down brute-force login/register attempts.
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,
  standardHeaders: true,
  legacyHeaders: false,
  message: { error: 'Too many attempts. Please try again later.' },
});

// POST /api/auth/register  — always creates a USER account.
// (Admin accounts are only created via seeding or by an existing admin
// through the admin user-management endpoints — a public registration
// form must never be able to grant itself elevated privileges.)
router.post('/register', authLimiter, validateRegister, async (req, res) => {
  const { fullName, email, password } = req.body;

  if (User.findByEmail(email)) {
    return res.status(409).json({ error: 'An account with this email already exists.' });
  }

  const user = await User.create({ fullName, email, password, role: User.ROLES.USER });
  const token = signAuthToken(user);
  res.status(201).json({ token, user: User.toPublic(user) });
});

// POST /api/auth/login
router.post('/login', authLimiter, validateLogin, async (req, res) => {
  const { email, password, rememberMe } = req.body;

  const user = User.findByEmail(email);
  // Same error message whether the email doesn't exist or the password is
  // wrong, so the endpoint doesn't leak which emails are registered.
  const invalid = () => res.status(401).json({ error: 'Invalid email or password.' });

  if (!user) return invalid();

  const valid = await User.verifyPassword(password, user.password);
  if (!valid) return invalid();

  const token = signAuthToken(user, { rememberMe: !!rememberMe });
  res.json({ token, user: User.toPublic(user), rememberMe: !!rememberMe });
});

// POST /api/auth/logout
// Stateless JWTs can't be revoked server-side without a blocklist; logout
// is primarily a client-side action (discard the token). This endpoint
// exists so the client has a real API to call and so a token blocklist can
// be added later without changing the frontend contract.
router.post('/logout', authenticate, (req, res) => {
  res.json({ success: true });
});

// GET /api/auth/me — used to restore a session on page reload.
router.get('/me', authenticate, (req, res) => {
  res.json({ user: req.user });
});

// POST /api/auth/forgot-password
router.post('/forgot-password', authLimiter, validateEmail, (req, res) => {
  const { email } = req.body;
  const user = User.findByEmail(email);

  // Always respond success so the endpoint can't be used to enumerate
  // which emails are registered.
  if (!user) {
    return res.json({ success: true, message: 'If that email is registered, a reset link has been sent.' });
  }

  const rawToken = generateResetToken();
  const data = db.read();
  data.resetTokens = data.resetTokens.filter(t => t.userId !== user.id); // invalidate old tokens
  data.resetTokens.push({
    userId: user.id,
    tokenHash: hashResetToken(rawToken),
    expiresAt: Date.now() + 15 * 60 * 1000, // 15 minutes
  });
  db.write(data);

  // No email service is configured in this project, so the reset link is
  // returned directly in the API response (dev-mode only) instead of being
  // silently dropped. Wire up a real mail provider (SendGrid, SES, etc.)
  // in production and remove `resetTokenForDev` from the response.
  res.json({
    success: true,
    message: 'If that email is registered, a reset link has been sent.',
    ...(process.env.NODE_ENV !== 'production' ? { resetTokenForDev: rawToken } : {}),
  });
});

// POST /api/auth/reset-password
router.post('/reset-password', authLimiter, validatePassword, async (req, res) => {
  const { token, password } = req.body;
  if (!token) return res.status(400).json({ error: 'Reset token is required.' });

  const tokenHash = hashResetToken(token);
  const data = db.read();
  const entry = data.resetTokens.find(t => t.tokenHash === tokenHash);

  if (!entry || entry.expiresAt < Date.now()) {
    return res.status(400).json({ error: 'This reset link is invalid or has expired.' });
  }

  await User.updatePassword(entry.userId, password);
  data.resetTokens = data.resetTokens.filter(t => t.tokenHash !== tokenHash);
  db.write(data);

  res.json({ success: true, message: 'Password has been reset. You can now log in.' });
});

// PUT /api/auth/change-password — for a logged-in user changing their own password.
router.put('/change-password', authenticate, validatePassword, async (req, res) => {
  const { currentPassword, password } = req.body;
  const user = User.findByEmail(req.user.email);

  const valid = await User.verifyPassword(currentPassword || '', user.password);
  if (!valid) return res.status(401).json({ error: 'Current password is incorrect.' });

  await User.updatePassword(user.id, password);
  res.json({ success: true, message: 'Password updated successfully.' });
});

export default router;

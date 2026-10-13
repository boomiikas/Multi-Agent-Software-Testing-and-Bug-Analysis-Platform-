import jwt from 'jsonwebtoken';
import crypto from 'crypto';

const JWT_SECRET = process.env.JWT_SECRET;
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '15m';
const JWT_REMEMBER_EXPIRES_IN = process.env.JWT_REMEMBER_EXPIRES_IN || '30d';

export function signAuthToken(user, { rememberMe = false } = {}) {
  const payload = { sub: user.id, email: user.email, role: user.role };
  const expiresIn = rememberMe ? JWT_REMEMBER_EXPIRES_IN : JWT_EXPIRES_IN;
  return jwt.sign(payload, JWT_SECRET, { expiresIn });
}

export function verifyAuthToken(token) {
  return jwt.verify(token, JWT_SECRET);
}

// Password-reset tokens are random opaque strings (not JWTs) so they can't
// be re-derived or reused for anything other than the single reset lookup
// stored server-side, and they carry their own expiry independent of login.
export function generateResetToken() {
  return crypto.randomBytes(32).toString('hex');
}

export function hashResetToken(token) {
  return crypto.createHash('sha256').update(token).digest('hex');
}

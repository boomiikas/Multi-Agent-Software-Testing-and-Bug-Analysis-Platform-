import { verifyAuthToken } from '../utils/token.js';
import { User } from '../models/User.js';

export function authenticate(req, res, next) {
  const header = req.headers.authorization || '';
  const [scheme, token] = header.split(' ');

  if (scheme !== 'Bearer' || !token) {
    return res.status(401).json({ error: 'Not authenticated. Missing or malformed token.' });
  }

  try {
    const payload = verifyAuthToken(token);
    const user = User.findById(payload.sub);
    if (!user) {
      return res.status(401).json({ error: 'Not authenticated. User no longer exists.' });
    }
    req.user = User.toPublic(user);
    next();
  } catch (err) {
    const message = err.name === 'TokenExpiredError' ? 'Session expired. Please log in again.' : 'Invalid token.';
    return res.status(401).json({ error: message });
  }
}

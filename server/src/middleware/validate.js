const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function isString(v) {
  return typeof v === 'string';
}

// Strips characters with no legitimate use in a name/email field and that
// are commonly used in NoSQL/HTML injection payloads ($, {, }, <, >).
export function sanitizeText(value) {
  if (!isString(value)) return value;
  return value.replace(/[<>${}]/g, '').trim();
}

export function validateRegister(req, res, next) {
  const { fullName, email, password } = req.body || {};
  const errors = [];

  if (!isString(fullName) || fullName.trim().length < 2) {
    errors.push('Full name must be at least 2 characters.');
  }
  if (!isString(email) || !EMAIL_RE.test(email)) {
    errors.push('A valid email is required.');
  }
  if (!isString(password) || password.length < 8) {
    errors.push('Password must be at least 8 characters.');
  } else if (!/[A-Z]/.test(password) || !/[0-9]/.test(password)) {
    errors.push('Password must include at least one uppercase letter and one number.');
  }

  if (errors.length) return res.status(400).json({ error: errors[0], errors });

  req.body.fullName = sanitizeText(fullName);
  req.body.email = sanitizeText(email).toLowerCase();
  next();
}

export function validateLogin(req, res, next) {
  const { email, password } = req.body || {};
  const errors = [];
  if (!isString(email) || !EMAIL_RE.test(email)) errors.push('A valid email is required.');
  if (!isString(password) || password.length < 1) errors.push('Password is required.');
  if (errors.length) return res.status(400).json({ error: errors[0], errors });
  req.body.email = sanitizeText(email).toLowerCase();
  next();
}

export function validateEmail(req, res, next) {
  const { email } = req.body || {};
  if (!isString(email) || !EMAIL_RE.test(email)) {
    return res.status(400).json({ error: 'A valid email is required.' });
  }
  req.body.email = sanitizeText(email).toLowerCase();
  next();
}

export function validatePassword(req, res, next) {
  const { password } = req.body || {};
  if (!isString(password) || password.length < 8) {
    return res.status(400).json({ error: 'Password must be at least 8 characters.' });
  }
  if (!/[A-Z]/.test(password) || !/[0-9]/.test(password)) {
    return res.status(400).json({ error: 'Password must include at least one uppercase letter and one number.' });
  }
  next();
}

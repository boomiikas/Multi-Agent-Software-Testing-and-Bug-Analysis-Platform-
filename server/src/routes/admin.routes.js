import { Router } from 'express';
import { User } from '../models/User.js';
import { authenticate } from '../middleware/auth.js';
import { authorize } from '../middleware/role.js';
import { sanitizeText } from '../middleware/validate.js';

const router = Router();

// Every route below requires a valid JWT AND the ADMIN role.
router.use(authenticate, authorize(User.ROLES.ADMIN));

// GET /api/admin/users
router.get('/users', (req, res) => {
  const users = User.findAll().map(User.toPublic);
  res.json({ users });
});

// POST /api/admin/users — admin creates a user (can assign either role)
router.post('/users', async (req, res) => {
  const { fullName, email, password, role } = req.body || {};

  if (!fullName || fullName.trim().length < 2) return res.status(400).json({ error: 'Full name must be at least 2 characters.' });
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return res.status(400).json({ error: 'A valid email is required.' });
  if (!password || password.length < 8) return res.status(400).json({ error: 'Password must be at least 8 characters.' });
  if (![User.ROLES.ADMIN, User.ROLES.USER].includes(role)) return res.status(400).json({ error: 'Role must be ADMIN or USER.' });

  if (User.findByEmail(email)) return res.status(409).json({ error: 'An account with this email already exists.' });

  const user = await User.create({ fullName: sanitizeText(fullName), email: sanitizeText(email).toLowerCase(), password, role });
  res.status(201).json({ user: User.toPublic(user) });
});

// PUT /api/admin/users/:id — edit name/email/role/profileImage
router.put('/users/:id', (req, res) => {
  const { id } = req.params;
  const target = User.findById(id);
  if (!target) return res.status(404).json({ error: 'User not found.' });

  const { fullName, email, role, profileImage } = req.body || {};
  const updates = {};

  if (fullName !== undefined) updates.fullName = sanitizeText(fullName);
  if (email !== undefined) {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return res.status(400).json({ error: 'A valid email is required.' });
    const existing = User.findByEmail(email);
    if (existing && existing.id !== id) return res.status(409).json({ error: 'Email already in use.' });
    updates.email = sanitizeText(email).toLowerCase();
  }
  if (role !== undefined) {
    if (![User.ROLES.ADMIN, User.ROLES.USER].includes(role)) return res.status(400).json({ error: 'Role must be ADMIN or USER.' });
    if (target.id === req.user.id && role !== User.ROLES.ADMIN) {
      return res.status(400).json({ error: 'You cannot demote your own account.' });
    }
    updates.role = role;
  }
  if (profileImage !== undefined) updates.profileImage = profileImage;

  const updated = User.update(id, updates);
  res.json({ user: User.toPublic(updated) });
});

// DELETE /api/admin/users/:id
router.delete('/users/:id', (req, res) => {
  const { id } = req.params;
  if (id === req.user.id) return res.status(400).json({ error: 'You cannot delete your own account.' });

  const target = User.findById(id);
  if (!target) return res.status(404).json({ error: 'User not found.' });

  User.remove(id);
  res.json({ success: true });
});

export default router;

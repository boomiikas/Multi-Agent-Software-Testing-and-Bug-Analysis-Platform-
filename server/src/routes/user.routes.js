import { Router } from 'express';
import { User } from '../models/User.js';
import { authenticate } from '../middleware/auth.js';
import { sanitizeText } from '../middleware/validate.js';

const router = Router();

router.use(authenticate);

// GET /api/users/profile
router.get('/profile', (req, res) => {
  res.json({ user: req.user });
});

// PUT /api/users/profile — a user editing their own name/profileImage.
// (Email and role changes are intentionally not allowed here — email
// changes should go through a verification flow, and role changes are an
// admin-only privilege handled in admin.routes.js.)
router.put('/profile', (req, res) => {
  const { fullName, profileImage } = req.body || {};
  const updates = {};
  if (fullName !== undefined) {
    if (!fullName || fullName.trim().length < 2) return res.status(400).json({ error: 'Full name must be at least 2 characters.' });
    updates.fullName = sanitizeText(fullName);
  }
  if (profileImage !== undefined) updates.profileImage = profileImage;

  const updated = User.update(req.user.id, updates);
  res.json({ user: User.toPublic(updated) });
});

export default router;

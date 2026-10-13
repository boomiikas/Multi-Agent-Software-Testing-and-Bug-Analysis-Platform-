import { User } from '../models/User.js';

export async function seedAdmin() {
  const email = process.env.DEFAULT_ADMIN_EMAIL || 'admin@example.com';
  const password = process.env.DEFAULT_ADMIN_PASSWORD || 'Admin@123';
  const fullName = process.env.DEFAULT_ADMIN_NAME || 'System Administrator';

  const existing = User.findByEmail(email);
  if (existing) return;

  await User.create({ fullName, email, password, role: User.ROLES.ADMIN });
  // eslint-disable-next-line no-console
  console.log(`[seed] Default admin created: ${email}`);
}

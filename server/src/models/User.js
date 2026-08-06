import bcrypt from 'bcryptjs';
import { v4 as uuidv4 } from 'uuid';
import { db } from '../config/db.js';

export const ROLES = Object.freeze({ ADMIN: 'ADMIN', USER: 'USER' });

const SALT_ROUNDS = 12;

function toPublic(user) {
  if (!user) return null;
  const { password, ...safe } = user;
  return safe;
}

function findAll() {
  return db.read().users;
}

function findByEmail(email) {
  if (!email) return null;
  return db.read().users.find(u => u.email.toLowerCase() === email.toLowerCase()) || null;
}

function findById(id) {
  return db.read().users.find(u => u.id === id) || null;
}

async function create({ fullName, email, password, role = ROLES.USER, profileImage = null }) {
  const data = db.read();
  const now = new Date().toISOString();
  const hashed = await bcrypt.hash(password, SALT_ROUNDS);
  const user = {
    id: uuidv4(),
    fullName,
    email: email.toLowerCase(),
    password: hashed,
    role,
    profileImage,
    createdAt: now,
    updatedAt: now,
  };
  data.users.push(user);
  db.write(data);
  return user;
}

function update(id, updates) {
  const data = db.read();
  const idx = data.users.findIndex(u => u.id === id);
  if (idx === -1) return null;
  data.users[idx] = { ...data.users[idx], ...updates, updatedAt: new Date().toISOString() };
  db.write(data);
  return data.users[idx];
}

async function updatePassword(id, newPassword) {
  const hashed = await bcrypt.hash(newPassword, SALT_ROUNDS);
  return update(id, { password: hashed });
}

function remove(id) {
  const data = db.read();
  const before = data.users.length;
  data.users = data.users.filter(u => u.id !== id);
  db.write(data);
  return data.users.length < before;
}

async function verifyPassword(plain, hashed) {
  return bcrypt.compare(plain, hashed);
}

export const User = {
  ROLES,
  toPublic,
  findAll,
  findByEmail,
  findById,
  create,
  update,
  updatePassword,
  remove,
  verifyPassword,
};

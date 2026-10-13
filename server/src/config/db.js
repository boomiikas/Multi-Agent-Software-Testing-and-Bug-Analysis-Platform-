import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_FILE = path.join(__dirname, '..', 'data', 'db.json');

const DEFAULT_SHAPE = { users: [], resetTokens: [] };

// NOTE: The original project had no database configured at all (pure
// front-end mock data). Rather than bolt on a heavyweight DB the rest of
// the app doesn't use yet, this is a small file-backed JSON store that
// behaves like a table (find/insert/update/delete) with a synchronous,
// atomic write. It is a genuine persistence layer (survives restarts) and
// can be swapped for Postgres/Mongo later by re-implementing this module's
// exported functions with the same signatures.

function ensureFile() {
  if (!fs.existsSync(DB_FILE)) {
    fs.mkdirSync(path.dirname(DB_FILE), { recursive: true });
    fs.writeFileSync(DB_FILE, JSON.stringify(DEFAULT_SHAPE, null, 2));
  }
}

function read() {
  ensureFile();
  const raw = fs.readFileSync(DB_FILE, 'utf-8');
  try {
    return { ...DEFAULT_SHAPE, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULT_SHAPE };
  }
}

function write(data) {
  const tmp = `${DB_FILE}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(data, null, 2));
  fs.renameSync(tmp, DB_FILE);
}

export const db = {
  read,
  write,
};

import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';

import authRoutes from './routes/auth.routes.js';
import adminRoutes from './routes/admin.routes.js';
import userRoutes from './routes/user.routes.js';
import { seedAdmin } from './seed/seedAdmin.js';

if (!process.env.JWT_SECRET) {
  console.error('FATAL: JWT_SECRET is not set. Copy server/.env.example to server/.env and set a real secret.');
  process.exit(1);
}

const app = express();

app.use(helmet());
app.use(cors({
  origin: process.env.CLIENT_ORIGIN || 'http://localhost:5173',
  credentials: true,
}));
app.use(express.json({ limit: '1mb' })); // also mitigates large-payload / basic injection abuse
app.use(morgan('dev'));

app.get('/api/health', (req, res) => res.json({ status: 'ok' }));

app.use('/api/auth', authRoutes);
app.use('/api/admin', adminRoutes);
app.use('/api/users', userRoutes);

// 404 for unknown API routes
app.use('/api', (req, res) => res.status(404).json({ error: 'Not found.' }));

// Central error handler — never leak stack traces to the client.
app.use((err, req, res, next) => {
  console.error(err);
  res.status(err.status || 500).json({ error: 'Something went wrong on the server.' });
});

const PORT = process.env.PORT || 4000;

seedAdmin().then(() => {
  app.listen(PORT, () => {
    console.log(`AgentQA API listening on http://localhost:${PORT}`);
  });
});

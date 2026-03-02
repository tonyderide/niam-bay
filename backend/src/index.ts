import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import recipesRoutes from './routes/recipes.routes';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.use('/api/recipes', recipesRoutes);

app.listen(PORT, () => {
  console.log(`NiamBay API running on port ${PORT}`);
});

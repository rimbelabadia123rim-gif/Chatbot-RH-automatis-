// API Next.js pour récupérer le nombre de notifications non lues
export default async function handler(req, res) {
  const { method, query } = req;
  const { matricule } = query;
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

  if (method === 'GET') {
    try {
      const response = await fetch(`${backendUrl}/notifications/${matricule}/count`);
      const data = await response.json();
      return res.status(200).json(data);
    } catch (error) {
      return res.status(500).json({ error: 'Erreur lors de la récupération du compteur' });
    }
  }

  return res.status(405).json({ error: 'Méthode non autorisée' });
}

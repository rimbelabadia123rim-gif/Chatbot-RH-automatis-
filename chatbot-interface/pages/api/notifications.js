// API Next.js pour gérer les notifications
export default async function handler(req, res) {
  const { method, query } = req;
  const { matricule } = query;
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

  if (method === 'GET') {
    // Récupérer les notifications d'un utilisateur
    const { unread_only } = query;
    const params = unread_only === 'true' ? '?unread_only=true' : '';
    
    try {
      const response = await fetch(`${backendUrl}/notifications/${matricule}${params}`);
      const data = await response.json();
      return res.status(200).json(data);
    } catch (error) {
      return res.status(500).json({ error: 'Erreur lors de la récupération des notifications' });
    }
  }

  if (method === 'POST') {
    // Marquer toutes les notifications comme lues
    try {
      const response = await fetch(`${backendUrl}/notifications/${matricule}/read-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      return res.status(200).json(data);
    } catch (error) {
      return res.status(500).json({ error: 'Erreur lors de la mise à jour des notifications' });
    }
  }

  return res.status(405).json({ error: 'Méthode non autorisée' });
}

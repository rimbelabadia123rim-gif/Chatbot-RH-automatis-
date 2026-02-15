// API Next.js pour relayer les requêtes admin RH vers le backend
export default async function handler(req, res) {
  const { method, headers, body, query } = req;
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';

  if (method === 'GET') {
    // Récupérer toutes les demandes de congé (RH)
    const userMatricule = headers['x-user-matricule'] || (body && body.matricule) || (query && query.matricule);
    if (!userMatricule) {
      return res.status(401).json({ error: 'Matricule RH requis' });
    }
    const response = await fetch(`${backendUrl}/admin/demandes-conge`, {
      method: 'GET',
      headers: { 'X-User-Matricule': userMatricule }
    });
    const data = await response.json();
    return res.status(200).json(data);
  }

  if (method === 'POST') {
    // Changer le statut d'une demande
    const { demande_id, status, matricule } = body;
    if (!demande_id || !status || !matricule) {
      return res.status(400).json({ error: 'Paramètres requis' });
    }
    const response = await fetch(`${backendUrl}/admin/demandes-conge/${demande_id}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-User-Matricule': matricule },
      body: JSON.stringify({ status })
    });
    const data = await response.json();
    return res.status(200).json(data);
  }

  return res.status(405).json({ error: 'Méthode non autorisée' });
}

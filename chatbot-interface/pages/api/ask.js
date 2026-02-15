// pages/api/ask.js
export default async function handler(req, res) {
  if (req.method === 'POST') {
    const { matricule, message } = req.body;

    try {
      console.log('Frontend API - Sending request to backend:', { matricule, message });
      
      const response = await fetch('http://localhost:8000/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ matricule, message }),
      });

      console.log('Backend response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Backend error response:', errorText);
        throw new Error('Erreur de communication avec le backend');
      }

      const data = await response.json();
      console.log('Backend response data:', data);
      res.status(200).json(data);
    } catch (error) {
      console.error('Frontend API error:', error);
      res.status(500).json({ error: error.message });
    }
  } else {
    res.status(405).json({ error: 'Méthode non autorisée' });
  }
}
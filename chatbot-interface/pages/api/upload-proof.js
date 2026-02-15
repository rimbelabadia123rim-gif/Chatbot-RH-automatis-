// pages/api/upload-proof.js
export const config = {
  api: {
    bodyParser: false,
  },
};

import formidable from 'formidable';
import fs from 'fs';
import FormData from 'form-data';
import fetch from 'node-fetch';

export default async function handler(req, res) {
  if (req.method === 'POST') {
    const form = formidable();
    form.parse(req, async (err, fields, files) => {
      if (err) {
        res.status(500).json({ error: 'Erreur lors du parsing du formulaire.' });
        return;
      }
      try {
        const formData = new FormData();
        formData.append('matricule', Array.isArray(fields.matricule) ? fields.matricule[0] : fields.matricule);
        let proofFile = files.proof;
        if (Array.isArray(proofFile)) proofFile = proofFile[0];
        if (proofFile && proofFile.filepath) {
          formData.append('proof', fs.createReadStream(proofFile.filepath), proofFile.originalFilename);
        }
        const response = await fetch('http://localhost:8000/upload-proof/', {
          method: 'POST',
          body: formData,
          headers: formData.getHeaders(),
        });
        const data = await response.json();
        console.log('Réponse backend upload-proof:', data); // Ajout du log
        if (!response.ok) {
          res.status(response.status).json(data);
          return;
        }
        res.status(200).json(data);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });
    return;
  }
  res.status(405).json({ error: 'Méthode non autorisée' });
}

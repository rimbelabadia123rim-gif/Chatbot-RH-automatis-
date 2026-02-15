// pages/api/submit-task.js
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
      // Utiliser formidable pour parser le form-data
      const form = formidable();
      form.parse(req, async (err, fields, files) => {
        if (err) {
          res.status(500).json({ error: 'Erreur lors du parsing du formulaire.' });
          return;
        }
        try {
          const formData = new FormData();
          // Champs texte
          formData.append('matricule', Array.isArray(fields.matricule) ? fields.matricule[0] : fields.matricule);
          formData.append('task_type', Array.isArray(fields.task_type) ? fields.task_type[0] : fields.task_type);
          formData.append('task_description', Array.isArray(fields.task_description) ? fields.task_description[0] : fields.task_description);
          // Fichier preuve (optionnel)
          if (files.proof) {
            formData.append('proof', fs.createReadStream(files.proof.filepath), files.proof.originalFilename);
          }
          // Appel FastAPI
          const response = await fetch('http://localhost:8000/submit-task/', {
            method: 'POST',
            body: formData,
            headers: formData.getHeaders(),
          });
          const data = await response.json();
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
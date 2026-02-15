import fs from 'fs';
import path from 'path';

export default async function handler(req, res) {
  const { file } = req.query;
  if (!file) {
    res.status(400).json({ error: 'Fichier requis' });
    return;
  }
  // Sécurité : empêcher la traversée de dossier
  if (file.includes('..') || file.includes('/')) {
    res.status(400).json({ error: 'Chemin invalide' });
    return;
  }
  const uploadsDir = path.resolve(process.cwd(), '../backend/app/uploads');
  const filePath = path.join(uploadsDir, file);
  if (!fs.existsSync(filePath)) {
    res.status(404).json({ error: 'Fichier non trouvé' });
    return;
  }
  // Détecter le content-type
  const ext = path.extname(file).toLowerCase();
  let contentType = 'application/octet-stream';
  if ([".jpg", ".jpeg"].includes(ext)) contentType = 'image/jpeg';
  else if (ext === ".png") contentType = 'image/png';
  else if (ext === ".gif") contentType = 'image/gif';
  else if (ext === ".pdf") contentType = 'application/pdf';

  // LOG DEBUG
  console.log(`[API/proof] Fichier servi: ${filePath} | Content-Type: ${contentType}`);

  res.setHeader('Content-Type', contentType);
  res.setHeader('Content-Disposition', `inline; filename="${file}"`);
  const stream = fs.createReadStream(filePath);
  stream.pipe(res);
}

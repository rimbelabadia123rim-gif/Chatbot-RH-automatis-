import { useState, useEffect } from 'react';
import Image from 'next/image';
import Navbar from '../components/Navbar';
import { useRouter } from 'next/router';

function RHPanel({ user, onClose }) {
  const [demandes, setDemandes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPreuve, setSelectedPreuve] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch('/api/admin-demandes', {
      method: 'GET',
      headers: { 'X-User-Matricule': user.matricule }
    })
      .then(res => res.json())
      .then(data => {
        setDemandes(data.demandes || []);
        setLoading(false);
      })
      .catch(() => {
        setError('Erreur lors du chargement.');
        setLoading(false);
      });
  }, [user]);

  const updateStatus = (id, status) => {
    setLoading(true);
    fetch('/api/admin-demandes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demande_id: id, status, matricule: user.matricule })
    })
      .then(res => res.json())
      .then(() => {
        setDemandes(demandes => demandes.map(d => d.id === id ? { ...d, status } : d));
        setLoading(false);
      })
      .catch(() => {
        setError('Erreur lors de la mise à jour.');
        setLoading(false);
      });
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(0,0,0,0.3)', zIndex: 50000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ background: '#fff', borderRadius: 12, padding: 24, minWidth: 600, maxHeight: '80vh', overflowY: 'auto', position: 'relative' }}>
        <h2>Liste des demandes de congé</h2>
        <button onClick={onClose} style={{ float: 'right', marginBottom: 12 }}>Fermer</button>
        {loading && <div>Chargement...</div>}
        {error && <div style={{ color: 'red' }}>{error}</div>}
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 16 }}>
          <thead>
            <tr>
              <th>Utilisateur</th>
              <th>Type</th>
              <th>Début</th>
              <th>Fin</th>
              <th>Raison</th>
              <th>Statut</th>
              <th>Preuve</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {demandes.map(d => (
              <tr key={d.id}>
                <td>{d.user.first_name} {d.user.last_name}</td>
                <td>{d.type_conge}</td>
                <td>{d.date_debut}</td>
                <td>{d.date_fin}</td>
                <td>{d.raison}</td>
                <td>{d.status}</td>
                <td>
                  {d.preuve ? (
                    <button 
                      style={{
                        background: '#6366f1', color: '#fff', border: 'none', borderRadius: 6, padding: '4px 12px', marginRight: 4, cursor: 'pointer', fontWeight: 500, boxShadow: '0 1px 4px #6366f133', transition: 'background 0.2s',
                        outline: 'none',
                      }}
                      onMouseOver={e => e.currentTarget.style.background = '#4f46e5'}
                      onMouseOut={e => e.currentTarget.style.background = '#6366f1'}
                      onClick={() => setSelectedPreuve(d.preuve.split(/[/\\]/).pop())}
                    >Voir preuve</button>
                  ) : 'Aucune'}
                </td>
                <td>
                  <button
                    disabled={d.status === 'validé'}
                    style={{
                      background: d.status === 'validé' ? '#22c55e55' : '#22c55e',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 6,
                      padding: '4px 12px',
                      marginRight: 4,
                      cursor: d.status === 'validé' ? 'not-allowed' : 'pointer',
                      fontWeight: 500,
                      boxShadow: '0 1px 4px #22c55e33',
                      transition: 'background 0.2s',
                      outline: 'none',
                    }}
                    onMouseOver={e => { if (d.status !== 'validé') e.currentTarget.style.background = '#16a34a'; }}
                    onMouseOut={e => { if (d.status !== 'validé') e.currentTarget.style.background = '#22c55e'; }}
                    onClick={() => updateStatus(d.id, 'validé')}
                  >Valider</button>
                  <button
                    disabled={d.status === 'refusé'}
                    style={{
                      background: d.status === 'refusé' ? '#ef444455' : '#ef4444',
                      color: '#fff',
                      border: 'none',
                      borderRadius: 6,
                      padding: '4px 12px',
                      cursor: d.status === 'refusé' ? 'not-allowed' : 'pointer',
                      fontWeight: 500,
                      boxShadow: '0 1px 4px #ef444433',
                      transition: 'background 0.2s',
                      outline: 'none',
                    }}
                    onMouseOver={e => { if (d.status !== 'refusé') e.currentTarget.style.background = '#b91c1c'; }}
                    onMouseOut={e => { if (d.status !== 'refusé') e.currentTarget.style.background = '#ef4444'; }}
                    onClick={() => updateStatus(d.id, 'refusé')}
                  >Refuser</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {selectedPreuve && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            background: 'rgba(0,0,0,0.45)',
            zIndex: 10000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <div style={{
              background: '#fff',
              borderRadius: 12,
              padding: 32,
              minWidth: 320,
              maxWidth: 600,
              maxHeight: '80vh',
              overflowY: 'auto',
              position: 'relative',
              boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}>
              <button
                onClick={() => setSelectedPreuve(null)}
                style={{
                  position: 'absolute',
                  top: 12,
                  right: 16,
                  background: 'transparent',
                  border: 'none',
                  fontSize: 28,
                  color: '#888',
                  cursor: 'pointer',
                  fontWeight: 700,
                  lineHeight: 1,
                  zIndex: 2,
                  transition: 'color 0.2s',
                }}
                aria-label="Fermer la preuve"
                onMouseOver={e => e.currentTarget.style.color = '#111'}
                onMouseOut={e => e.currentTarget.style.color = '#888'}
              >×</button>
              <h3 style={{ marginBottom: 24 }}>Preuve</h3>
              {selectedPreuve.match(/\.(jpg|jpeg|png|gif)$/i) ? (
                <img src={`/api/proof?file=${encodeURIComponent(selectedPreuve)}`} alt="preuve" style={{ maxWidth: 480, maxHeight: 400, borderRadius: 8, boxShadow: '0 2px 8px #0001' }} />
              ) : selectedPreuve.match(/\.pdf$/i) ? (
                <embed
                  src={`/api/proof?file=${encodeURIComponent(selectedPreuve)}`}
                  type="application/pdf"
                  style={{ width: 480, height: 500, borderRadius: 8, boxShadow: '0 2px 8px #0001' }}
                />
              ) : (
                <a href={`/api/proof?file=${encodeURIComponent(selectedPreuve)}`} target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb', fontWeight: 500, fontSize: 18 }}>Télécharger le fichier</a>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Home() {
  const [message, setMessage] = useState('');
  const [matricule, setMatricule] = useState('');
  const [user, setUser] = useState(null); // { matricule, first_name, last_name }
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [taskType, setTaskType] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [proofFile, setProofFile] = useState(null);
  const [showProofUpload, setShowProofUpload] = useState(false);
  const [proofUploadMessage, setProofUploadMessage] = useState('');
  const [loginMatricule, setLoginMatricule] = useState('');
  const [loginError, setLoginError] = useState('');
  const [showRHPanel, setShowRHPanel] = useState(false); // État pour afficher le panneau RH
  const [selectedProof, setSelectedProof] = useState(null); // <-- Ajouté ici, global
  const router = useRouter();

  useEffect(() => {
    // Vérifier la session utilisateur
    const storedUser = typeof window !== 'undefined' ? localStorage.getItem('user') : null;
    if (storedUser) {
      const parsed = JSON.parse(storedUser);
      setUser(parsed);
      setMatricule(parsed.matricule);
    }
  }, []);

  // Connexion utilisateur via le champ dans la navbar
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoading(true);
    try {
      // Appel backend pour récupérer les infos utilisateur
      const res = await fetch(`/api/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ matricule: loginMatricule, message: '' })
      });
      const data = await res.json();
      // On suppose que le backend renvoie le nom/prénom dans la réponse si matricule valide
      if (data && data.response && data.response.includes('prénom')) {
        // Correction du parsing prénom/nom pour éviter doublon
        // Exemples de réponse : "Votre prénom est : John\nVotre nom est : Doe"
        let first_name = '';
        let last_name = '';
        // Extraction ligne par ligne pour éviter doublon
        const lines = data.response.split('\n');
        for (const line of lines) {
          const prenomMatch = line.match(/pr[ée]nom est ?: ?([\w-]+)/i);
          if (prenomMatch) first_name = prenomMatch[1];
          const nomMatch = line.match(/nom est ?: ?([\w-]+)/i);
          if (nomMatch) last_name = nomMatch[1];
        }
        const userObj = { matricule: loginMatricule, first_name, last_name };
        setUser(userObj);
        setMatricule(loginMatricule);
        localStorage.setItem('user', JSON.stringify(userObj));
        setLoginMatricule('');
        // Message de bienvenue personnalisé
        setChatHistory([{ sender: 'bot', text: `Bonjour ${first_name} ${last_name}, comment je peux vous aidez aujourd'hui ? ` }]);
      } else {
        setLoginError('Matricule inconnu ou erreur de connexion.');
      }
    } catch (err) {
      setLoginError('Erreur réseau.');
    }
    setLoading(false);
  };

  // Déconnexion
  const handleLogout = () => {
    setUser(null);
    setMatricule('');
    localStorage.removeItem('user');
    setChatHistory([]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ matricule, message }),
      });

      const data = await res.json();
      // Correction : gestion spéciale pour la réponse RH structurée
      if (data.demandes_conges_structurees) {
        setChatHistory((prev) => [
          ...prev,
          { sender: 'user', text: message },
          { sender: 'bot', text: 'demandes_conges_structurees', demandes: data.demandes_conges_structurees }
        ]);
        setMessage('');
        setLoading(false);
        return;
      }
      
      // Gestion spéciale pour les logs structurés
      if (data.logs_structurees) {
        setChatHistory((prev) => [
          ...prev,
          { sender: 'user', text: message },
          { 
            sender: 'bot', 
            text: 'chat_history_structuree', 
            logs_structurees: data.logs_structurees,
            total: data.total,
            periode: data.periode
          }
        ]);
        setMessage('');
        setLoading(false);
        return;
      }
      
      // Gestion spéciale pour les rapports générés avec bouton de téléchargement
      if (data.report_file || data.download_url || data.show_download_button) {
        setChatHistory((prev) => [
          ...prev,
          { sender: 'user', text: message },
          { 
            sender: 'bot', 
            text: data.response,
            report_file: data.report_file,
            download_url: data.download_url,
            show_download_button: data.show_download_button,
            report_type: data.report_type,
            filename: data.filename
          }
        ]);
        setMessage('');
        setLoading(false);
        return;
      }
      
      // Correction : toujours afficher la réponse du backend, même si elle est vide ou custom
      let botResponse = data.response;
      if (!botResponse && data.error) botResponse = data.error;
      if (!botResponse) botResponse = 'Désolé, je n\'ai pas compris.';

      setChatHistory((prev) => [
        ...prev,
        { sender: 'user', text: message },
        { sender: 'bot', text: botResponse },
      ]);

      if (data.show_form) {
        setShowForm(true);
        setTaskType(data.task_type);
      }
      // Afficher le formulaire d'upload de preuve 
      if (data.requestFile) {
        setShowProofUpload(true);
        setProofUploadMessage(botResponse);
      }

      setMessage('');
    } catch (error) {
      console.error('Erreur:', error);
      setChatHistory((prev) => [
        ...prev,
        { sender: 'bot', text: 'Erreur lors de la communication avec le backend.' },
      ]);
    }

    setLoading(false);
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('matricule', matricule);
      formData.append('task_type', taskType);
      formData.append('task_description', taskDescription);
      if (proofFile) {
        formData.append('proof', proofFile);
      }
      const res = await fetch('/api/submit-task', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setChatHistory((prev) => [
        ...prev,
        { sender: 'bot', text: data.response },
      ]);
      setShowForm(false); // Fermer le formulaire
      setTaskDescription(''); // Réinitialiser le champ de description
      setProofFile(null); // Réinitialiser le fichier
    } catch (error) {
      console.error('Erreur:', error);
      setChatHistory((prev) => [
        ...prev,
        { sender: 'bot', text: 'Erreur lors de la soumission du formulaire.' },
      ]);
    }
    setLoading(false);
  };

  const handleProofUpload = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('matricule', matricule);
      formData.append('proof', proofFile);
      const res = await fetch('/api/upload-proof', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      let botText = data.response || data.error || "Erreur lors de l'upload du fichier preuve.";
      // Ajout du pourcentage et de l'explication si présents
      if (data.acceptance_percentage !== undefined && data.explanation) {
        botText += `\n\nProbabilité d'acceptation : ${data.acceptance_percentage}%\n${data.explanation}`;
      }
      setChatHistory((prev) => [
        ...prev,
        { sender: 'bot', text: botText },
      ]);
      setShowProofUpload(false);
      setProofFile(null);
      setProofUploadMessage('');
    } catch (error) {
      setChatHistory((prev) => [
        ...prev,
        { sender: 'bot', text: "Erreur lors de l'upload du fichier preuve." },
      ]);
    }
    setLoading(false);
  };

  // Fonction utilitaire pour parser le tableau textuel d'historique de congés
  function parseCongeTable(text) {
    // Détecte le bloc tableau et la légende
    const tableauStart = text.indexOf('Type');
    const legendeStart = text.indexOf('Légende');
    if (tableauStart === -1) return null;
    const tableauText = text.substring(tableauStart, legendeStart !== -1 ? legendeStart : undefined).trim();
    const legendeText = legendeStart !== -1 ? text.substring(legendeStart).trim() : '';
    const lines = tableauText.split('\n').filter(l => l.trim() && !/^[- ]+$/.test(l));
    if (lines.length < 2) return null;
    const headers = lines[0].split(/\s{2,}/).map(h => h.trim());
    const rows = lines.slice(1).map(line => line.match(/(.{15}) (.{12}) (.{12}) (.{25}) (.{12}) (.{16})/)).filter(Boolean).map(match => match.slice(1).map(cell => cell.trim()));
    return { headers, rows, legende: legendeText };
  }

  // Fonction utilitaire pour parser un tableau textuel générique (colonnes dynamiques)
  function parseTextTable(text) {
    // Cherche la première ligne d'en-tête (au moins 2 colonnes séparées par 2+ espaces)
    const lines = text.split('\n').filter(l => l.trim());
    const headerIdx = lines.findIndex(l => l.match(/\s{2,}/));
    if (headerIdx === -1) return null;
    const headers = lines[headerIdx].split(/\s{2,}/).map(h => h.trim());
    // Les lignes suivantes sont les données (même nombre de colonnes)
    const rows = [];
    for (let i = headerIdx + 1; i < lines.length; i++) {
      const row = lines[i].split(/\s{2,}/).map(cell => cell.trim());
      if (row.length === headers.length) rows.push(row);
    }
    if (rows.length === 0) return null;
    return { headers, rows };
  }

  // Fonction pour réinitialiser le chat
  const handleNewChat = () => {
    setChatHistory([]);
    setShowForm(false);
    setTaskType('');
    setTaskDescription('');
    setProofFile(null);
    setShowProofUpload(false);
    setProofUploadMessage('');
    setMessage('');
  };

  // Fonction pour gérer le statut RH (validation/refus)
  const handleRHStatus = async (id, status) => {
    setLoading(true);
    try {
      await fetch('/api/admin-demandes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ demande_id: id, status, matricule })
      });
      // Optionnel : rafraîchir le chat ou afficher un message de succès
    } catch (e) {
      alert('Erreur lors de la mise à jour du statut.');
    }
    setLoading(false);
  };

  return (
    <div style={styles.container}>
      {/* Navbar en haut de la page, bouton à gauche et logo */}
      <Navbar
        user={user}
        loginMatricule={loginMatricule}
        setLoginMatricule={setLoginMatricule}
        handleLogin={handleLogin}
        loading={loading}
        loginError={loginError}
        handleLogout={handleLogout}
        handleNewChat={handleNewChat}
        styles={styles}
        showHistoryButton={true}
        onHistoryClick={() => router.push('/historique')}
      />
      {/* Conteneur du chatbot */}
      <div style={styles.chatContainer}>
        {/* En-tête du chatbot */}
        <div style={styles.header}>
          <h1 style={styles.headerTitle}>Chatbot Assistant</h1>
          <p style={styles.headerSubtitle}>Comment puis-je vous aider aujourd'hui ?</p>
        </div>

        {/* Zone de conversation */}
        <div style={styles.chatArea}>
          {chatHistory.map((chat, index) => {
            // Affichage RH : tableau structuré avec actions si réponse structurée
            if (
              chat.sender === 'bot' &&
              chat.text === 'demandes_conges_structurees' &&
              chat.demandes && Array.isArray(chat.demandes)
            ) {
              const handleRHStatusWithRefresh = async (id, status) => {
                setLoading(true);
                try {
                  await fetch('/api/admin-demandes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ demande_id: id, status, matricule })
                  });
                  // Rafraîchir la liste RH dans le chat en redemandant le tableau au backend
                  const res = await fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ matricule, message: 'liste des congés' })
                  });
                  const data = await res.json();
                  setChatHistory((prev) => prev.map((c, idx) =>
                    idx === index ? { ...c, demandes: data.demandes_conges_structurees || data.demandes || [] } : c
                  ));
                } catch (e) {
                  alert('Erreur lors de la mise à jour du statut.');
                }
                setLoading(false);
              };
              return (
                <div key={index} style={{ ...styles.messageContainer, justifyContent: 'flex-start' }}>
                  <div style={{ ...styles.messageBubble, backgroundColor: '#f3f4f6', color: '#000', borderRadius: '12px 12px 12px 0', maxWidth: '100%' }}>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '0.9rem', marginBottom: 8 }}>
                        <thead>
                          <tr>
                            <th>Utilisateur</th>
                            <th>Type</th>
                            <th>Début</th>
                            <th>Fin</th>
                            <th>Raison</th>
                            <th>Statut</th>
                            <th>Preuve</th>
                            <th>Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {chat.demandes.map((d) => (
                            <tr key={d.id}>
                              <td>{d.first_name} {d.last_name}</td>
                              <td>{d.type_conge}</td>
                              <td>{d.date_debut}</td>
                              <td>{d.date_fin}</td>
                              <td>{d.raison}</td>
                              <td>{d.statut}</td>
                              <td>
                                {d.preuve ? (
                                  <button 
                                    style={{
                                      background: '#6366f1', color: '#fff', border: 'none', borderRadius: 6, padding: '4px 12px', marginRight: 4, cursor: 'pointer', fontWeight: 500, boxShadow: '0 1px 4px #6366f133', transition: 'background 0.2s',
                                      outline: 'none',
                                    }}
                                    onMouseOver={e => e.currentTarget.style.background = '#4f46e5'}
                                    onMouseOut={e => e.currentTarget.style.background = '#6366f1'}
                                    onClick={() => setSelectedProof(d.preuve.split(/[/\\]/).pop())}
                                  >Voir preuve</button>
                                ) : 'Aucune'}
                              </td>
                              <td>
                                <button
                                  disabled={d.statut === 'validé'}
                                  style={{
                                    background: d.statut === 'validé' ? '#22c55e55' : '#22c55e',
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: 6,
                                    padding: '4px 12px',
                                    marginRight: 4,
                                    cursor: d.statut === 'validé' ? 'not-allowed' : 'pointer',
                                    fontWeight: 500,
                                    boxShadow: '0 1px 4px #22c55e33',
                                    transition: 'background 0.2s',
                                    outline: 'none',
                                  }}
                                  onMouseOver={e => { if (d.statut !== 'validé') e.currentTarget.style.background = '#16a34a'; }}
                                  onMouseOut={e => { if (d.statut !== 'validé') e.currentTarget.style.background = '#22c55e'; }}
                                  onClick={() => handleRHStatusWithRefresh(d.id, 'validé')}
                                >Valider</button>
                                <button
                                  disabled={d.statut === 'refusé'}
                                  style={{
                                    background: d.statut === 'refusé' ? '#ef444455' : '#ef4444',
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: 6,
                                    padding: '4px 12px',
                                    cursor: d.statut === 'refusé' ? 'not-allowed' : 'pointer',
                                    fontWeight: 500,
                                    boxShadow: '0 1px 4px #ef444433',
                                    transition: 'background 0.2s',
                                    outline: 'none',
                                  }}
                                  onMouseOver={e => { if (d.statut !== 'refusé') e.currentTarget.style.background = '#dc2626'; }}
                                  onMouseOut={e => { if (d.statut !== 'refusé') e.currentTarget.style.background = '#ef4444'; }}
                                  onClick={() => handleRHStatusWithRefresh(d.id, 'refusé')}
                                >Refuser</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              );
            }
            
            // Affichage des logs structurés
            if (
              chat.sender === 'bot' &&
              chat.text === 'chat_history_structuree' &&
              chat.logs_structurees && Array.isArray(chat.logs_structurees)
            ) {
              return (
                <div key={index} style={{ ...styles.messageContainer, justifyContent: 'flex-start' }}>
                  <div style={{ ...styles.messageBubble, backgroundColor: '#f3f4f6', color: '#000', borderRadius: '12px 12px 12px 0', maxWidth: '100%' }}>
                    <h4 style={{ margin: '0 0 16px 0', color: '#374151', fontSize: '1.1rem' }}>
                      📋 HISTORIQUE DE VOS CONVERSATIONS
                    </h4>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ 
                        borderCollapse: 'collapse', 
                        width: '100%', 
                        fontSize: '0.9rem', 
                        marginBottom: 16,
                        border: '1px solid #d1d5db',
                        borderRadius: '8px',
                        overflow: 'hidden'
                      }}>
                        <thead>
                          <tr style={{ backgroundColor: '#e0e7ff' }}>
                            <th style={{ 
                              border: '1px solid #d1d5db', 
                              padding: '12px 8px', 
                              textAlign: 'left',
                              fontWeight: '600',
                              color: '#374151'
                            }}>Date</th>
                            <th style={{ 
                              border: '1px solid #d1d5db', 
                              padding: '12px 8px', 
                              textAlign: 'left',
                              fontWeight: '600',
                              color: '#374151'
                            }}>Auteur</th>
                            <th style={{ 
                              border: '1px solid #d1d5db', 
                              padding: '12px 8px', 
                              textAlign: 'left',
                              fontWeight: '600',
                              color: '#374151'
                            }}>Message</th>
                          </tr>
                        </thead>
                        <tbody>
                          {chat.logs_structurees.map((log, i) => (
                            <tr key={log.id} style={{ 
                              backgroundColor: i % 2 === 0 ? '#ffffff' : '#f9fafb',
                              transition: 'background-color 0.2s'
                            }}
                            onMouseOver={e => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                            onMouseOut={e => e.currentTarget.style.backgroundColor = i % 2 === 0 ? '#ffffff' : '#f9fafb'}
                            >
                              <td style={{ 
                                border: '1px solid #e5e7eb', 
                                padding: '10px 8px',
                                fontSize: '0.85rem',
                                color: '#6b7280'
                              }}>{log.date}</td>
                              <td style={{ 
                                border: '1px solid #e5e7eb', 
                                padding: '10px 8px',
                                fontWeight: '500'
                              }}>{log.auteur}</td>
                              <td style={{ 
                                border: '1px solid #e5e7eb', 
                                padding: '10px 8px',
                                wordBreak: 'break-word',
                                maxWidth: '400px'
                              }}>{log.message}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginTop: '12px',
                      padding: '8px 0',
                      borderTop: '1px solid #e5e7eb',
                      fontSize: '0.85rem',
                      color: '#6b7280'
                    }}>
                      <span>📊 Total: {chat.total} message(s)</span>
                      <span>📅 {chat.periode}</span>
                    </div>
                    <div style={{
                      marginTop: '8px',
                      fontSize: '0.8rem',
                      color: '#9ca3af',
                      fontStyle: 'italic'
                    }}>
                      💡 Conseil: Tapez 'nouveau chat' pour effacer l'historique
                    </div>
                  </div>
                </div>
              );
            }
            
            // Affichage spécial pour les rapports avec bouton de téléchargement
              const handleRHStatusWithRefresh = async (id, status) => {
                setLoading(true);
                try {
                  await fetch('/api/admin-demandes', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ demande_id: id, status, matricule })
                  });
                  // Rafraîchir la liste RH dans le chat en redemandant le tableau au backend
                  const res = await fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ matricule, message: 'liste des congés' })
                  });
                  const data = await res.json();
                  setChatHistory((prev) => prev.map((c, idx) =>
                    idx === index ? { ...c, demandes: data.demandes_conges_structurees || data.demandes || [] } : c
                  ));
                } catch (e) {
                  alert('Erreur lors de la mise à jour du statut.');
                }
                setLoading(false);
              };
              return (
                <div key={index} style={{ ...styles.messageContainer, justifyContent: 'flex-start' }}>
                  <div style={{ ...styles.messageBubble, backgroundColor: '#f3f4f6', color: '#000', borderRadius: '12px 12px 12px 0', maxWidth: '100%' }}>
                    <div style={{ overflowX: 'auto' }}>
                      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '0.9rem', marginBottom: 8 }}>
                        <thead>
                          <tr>
                            <th>Utilisateur</th>
                            <th>Type</th>
                            <th>Début</th>
                            <th>Fin</th>
                            <th>Raison</th>
                            <th>Statut</th>
                            <th>Preuve</th>
                            <th>Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {chat.demandes.map((d) => (
                            <tr key={d.id}>
                              <td>{d.first_name} {d.last_name}</td>
                              <td>{d.type_conge}</td>
                              <td>{d.date_debut}</td>
                              <td>{d.date_fin}</td>
                              <td>{d.raison}</td>
                              <td>{d.statut}</td>
                              <td>
                                {d.preuve ? (
                                  <button 
                                    style={{
                                      background: '#6366f1', color: '#fff', border: 'none', borderRadius: 6, padding: '4px 12px', marginRight: 4, cursor: 'pointer', fontWeight: 500, boxShadow: '0 1px 4px #6366f133', transition: 'background 0.2s',
                                      outline: 'none',
                                    }}
                                    onMouseOver={e => e.currentTarget.style.background = '#4f46e5'}
                                    onMouseOut={e => e.currentTarget.style.background = '#6366f1'}
                                    onClick={() => setSelectedProof(d.preuve.split(/[/\\]/).pop())}
                                  >Voir preuve</button>
                                ) : 'Aucune'}
                              </td>
                              <td>
                                <button
                                  disabled={d.statut === 'validé'}
                                  style={{
                                    background: d.statut === 'validé' ? '#22c55e55' : '#22c55e',
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: 6,
                                    padding: '4px 12px',
                                    marginRight: 4,
                                    cursor: d.statut === 'validé' ? 'not-allowed' : 'pointer',
                                    fontWeight: 500,
                                    boxShadow: '0 1px 4px #22c55e33',
                                    transition: 'background 0.2s',
                                    outline: 'none',
                                  }}
                                  onMouseOver={e => { if (d.statut !== 'validé') e.currentTarget.style.background = '#16a34a'; }}
                                  onMouseOut={e => { if (d.statut !== 'validé') e.currentTarget.style.background = '#22c55e'; }}
                                  onClick={() => handleRHStatusWithRefresh(d.id, 'validé')}
                                >Valider</button>
                                <button
                                  disabled={d.statut === 'refusé'}
                                  style={{
                                    background: d.statut === 'refusé' ? '#ef444455' : '#ef4444',
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: 6,
                                    padding: '4px 12px',
                                    cursor: d.statut === 'refusé' ? 'not-allowed' : 'pointer',
                                    fontWeight: 500,
                                    boxShadow: '0 1px 4px #ef444433',
                                    transition: 'background 0.2s',
                                    outline: 'none',
                                  }}
                                  onMouseOver={e => { if (d.statut !== 'refusé') e.currentTarget.style.background = '#b91c1c'; }}
                                  onMouseOut={e => { if (d.statut !== 'refusé') e.currentTarget.style.background = '#ef4444'; }}
                                  onClick={() => handleRHStatusWithRefresh(d.id, 'refusé')}
                                >Refuser</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {/* Modale d’aperçu de preuve */}
                    {selectedProof && (
                      <div style={{
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        width: '100vw',
                        height: '100vh',
                        background: 'rgba(0,0,0,0.45)',
                        zIndex: 10000,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}>
                        <div style={{
                          background: '#fff',
                          borderRadius: 12,
                          padding: 32,
                          minWidth: 320,
                          maxWidth: 600,
                          maxHeight: '80vh',
                          overflowY: 'auto',
                          position: 'relative',
                          boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                        }}>
                          <button
                            onClick={() => setSelectedProof(null)}
                            style={{
                              position: 'absolute',
                              top: 12,
                              right: 16,
                              background: 'transparent',
                              border: 'none',
                              fontSize: 28,
                              color: '#888',
                              cursor: 'pointer',
                              fontWeight: 700,
                              lineHeight: 1,
                              zIndex: 2,
                              transition: 'color 0.2s',
                            }}
                            aria-label="Fermer la preuve"
                            onMouseOver={e => e.currentTarget.style.color = '#111'}
                            onMouseOut={e => e.currentTarget.style.color = '#888'}
                          >×</button>
                          <h3 style={{ marginBottom: 24 }}>Preuve</h3>
                          {selectedProof.match(/\.(jpg|jpeg|png|gif)$/i) ? (
                            <img src={`/api/proof?file=${encodeURIComponent(selectedProof)}`} alt="preuve" style={{ maxWidth: 480, maxHeight: 400, borderRadius: 8, boxShadow: '0 2px 8px #0001' }} />
                          ) : selectedProof.match(/\.pdf$/i) ? (
                            <embed
                              src={`/api/proof?file=${encodeURIComponent(selectedProof)}`}
                              type="application/pdf"
                              style={{ width: 480, height: 500, borderRadius: 8, boxShadow: '0 2px 8px #0001' }}
                            />
                          ) : (
                            <a href={`/api/proof?file=${encodeURIComponent(selectedProof)}`} target="_blank" rel="noopener noreferrer" style={{ color: '#2563eb', fontWeight: 500, fontSize: 18 }}>Télécharger le fichier</a>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            }
            // Affichage spécial pour les rapports avec bouton de téléchargement
            if (chat.sender === 'bot' && chat.show_download_button && chat.download_url) {
              return (
                <div
                  key={index}
                  style={{
                    ...styles.messageContainer,
                    justifyContent: 'flex-start',
                  }}
                >
                  <div
                    style={{
                      ...styles.messageBubble,
                      backgroundColor: '#f3f4f6',
                      color: '#000',
                      borderRadius: '12px 12px 12px 0',
                      maxWidth: '90%',
                    }}
                  >
                    <p style={styles.messageText}>{chat.text}</p>
                    {/* Bouton de téléchargement stylé */}
                    <div style={{ 
                      display: 'flex', 
                      justifyContent: 'center', 
                      marginTop: '12px',
                      paddingTop: '12px',
                      borderTop: '1px solid #e5e7eb'
                    }}>
                      <a
                        href={chat.download_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '8px',
                          backgroundColor: '#3b82f6',
                          color: '#fff',
                          padding: '10px 20px',
                          borderRadius: '8px',
                          textDecoration: 'none',
                          fontWeight: '600',
                          fontSize: '14px',
                          transition: 'all 0.2s ease',
                          boxShadow: '0 2px 4px rgba(59, 130, 246, 0.2)',
                          cursor: 'pointer',
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.backgroundColor = '#2563eb';
                          e.currentTarget.style.transform = 'translateY(-1px)';
                          e.currentTarget.style.boxShadow = '0 4px 8px rgba(59, 130, 246, 0.3)';
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.backgroundColor = '#3b82f6';
                          e.currentTarget.style.transform = 'translateY(0)';
                          e.currentTarget.style.boxShadow = '0 2px 4px rgba(59, 130, 246, 0.2)';
                        }}
                      >
                        <span>📥</span>
                        Télécharger le rapport {chat.report_type === 'charge' ? 'de charge' : 'de congés'}
                      </a>
                    </div>
                  </div>
                </div>
              );
            }
            // Affichage enrichi si c'est l'historique de vos demandes de congé
            if (
              chat.sender === 'bot' &&
              typeof chat.text === 'string' &&
              chat.text.startsWith("Voici l'historique de vos demandes de congé :")
            ) {
              const parsed = parseCongeTable(chat.text);
              if (parsed) {
                return (
                  <div key={index} style={{ ...styles.messageContainer, justifyContent: 'flex-start' }}>
                    <div style={{ ...styles.messageBubble, backgroundColor: '#f3f4f6', color: '#000', borderRadius: '12px 12px 12px 0', maxWidth: '100%' }}>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '0.9rem', marginBottom: 8 }}>
                          <thead>
                            <tr>
                              {parsed.headers.map((h, i) => (
                                <th key={i} style={{ borderBottom: '1px solid #ccc', padding: '4px 8px', background: '#e0e7ff', textAlign: 'left' }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {parsed.rows.map((row, i) => (
                              <tr key={i}>
                                {row.map((cell, j) => (
                                  <td key={j} style={{ borderBottom: '1px solid #eee', padding: '4px 8px', whiteSpace: 'pre' }}>{cell}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {parsed.legende && <div style={{ color: '#6b7280', fontSize: '0.85em', whiteSpace: 'pre-line' }}>{parsed.legende}</div>}
                      </div>
                    </div>
                  </div>
                );
              }
            }
            // Affichage enrichi si c'est l'historique de chat sous forme de tableau textuel
            if (
              chat.sender === 'bot' &&
              typeof chat.text === 'string' &&
              chat.text.startsWith('Historique de chat :')
            ) {
              const parsed = parseTextTable(chat.text.replace('Historique de chat :', ''));
              if (parsed) {
                return (
                  <div key={index} style={{ ...styles.messageContainer, justifyContent: 'flex-start' }}>
                    <div style={{ ...styles.messageBubble, backgroundColor: '#f3f4f6', color: '#000', borderRadius: '12px 12px 12px 0', maxWidth: '100%' }}>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '0.9rem', marginBottom: 8 }}>
                          <thead>
                            <tr>
                              {parsed.headers.map((h, i) => (
                                <th key={i} style={{ borderBottom: '1px solid #ccc', padding: '4px 8px', background: '#e0e7ff', textAlign: 'left' }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {parsed.rows.map((row, i) => (
                              <tr key={i}>
                                {row.map((cell, j) => (
                                  <td key={j} style={{ borderBottom: '1px solid #eee', padding: '4px 8px', whiteSpace: 'pre' }}>{cell}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                );
              }
            }
            // Affichage enrichi si c'est la réponse info user (tableau textuel structuré)
            if (
              chat.sender === 'bot' &&
              typeof chat.text === 'string' &&
              chat.text.startsWith("Informations de l'utilisateur ") && chat.text.includes('Champ') && chat.text.includes('Valeur')
            ) {
              const parsed = parseTextTable(chat.text.replace(/^Informations de l'utilisateur [^:]+:/, ''));
              if (parsed) {
                // Extraire la légende si présente
                const legendeMatch = chat.text.match(/Légende[\s\S]*$/);
                const legende = legendeMatch ? legendeMatch[0] : '';
                return (
                  <div key={index} style={{ ...styles.messageContainer, justifyContent: 'flex-start' }}>
                    <div style={{ ...styles.messageBubble, backgroundColor: '#f3f4f6', color: '#000', borderRadius: '12px 12px 12px 0', maxWidth: '100%' }}>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: '0.9rem', marginBottom: 8 }}>
                          <thead>
                            <tr>
                              {parsed.headers.map((h, i) => (
                                <th key={i} style={{ borderBottom: '1px solid #ccc', padding: '4px 8px', background: '#e0e7ff', textAlign: 'left' }}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {parsed.rows.map((row, i) => (
                              <tr key={i}>
                                {row.map((cell, j) => (
                                  <td key={j} style={{ borderBottom: '1px solid #eee', padding: '4px 8px', whiteSpace: 'pre' }}>{cell}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {legende && <div style={{ color: '#6b7280', fontSize: '0.85em', whiteSpace: 'pre-line' }}>{legende}</div>}
                      </div>
                    </div>
                  </div>
                );
              }
            }
            // Affichage classique sinon
            return (
              <div
                key={index}
                style={{
                  ...styles.messageContainer,
                  justifyContent: chat.sender === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div
                  style={{
                    ...styles.messageBubble,
                    backgroundColor: chat.sender === 'user' ? '#3b82f6' : '#f3f4f6',
                    color: chat.sender === 'user' ? '#fff' : '#000',
                    borderRadius:
                      chat.sender === 'user'
                        ? '12px 12px 0 12px'
                        : '12px 12px 12px 0',
                  }}
                >
                  <p style={styles.messageText}>{chat.text}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Formulaire pour la création de tâches */}
        {showForm && (
          <div style={styles.formContainer}>
            <form onSubmit={handleFormSubmit} style={styles.inputForm} encType="multipart/form-data">
              <input
                type="text"
                value={taskType}
                readOnly
                style={styles.inputField}
              />
              <textarea
                value={taskDescription}
                onChange={(e) => setTaskDescription(e.target.value)}
                placeholder="Description de la tâche..."
                style={styles.inputField}
                required
              />
              <input
                type="file"
                name="proof"
                accept="application/pdf,image/*"
                onChange={e => setProofFile(e.target.files[0])}
                style={{ flex: 1 }}
              />
              <button
                type="submit"
                disabled={loading}
                style={styles.sendButton}
              >
                {loading ? (
                  <div style={styles.spinner}></div>
                ) : (
                  'Valider'
                )}
              </button>
            </form>
          </div>
        )}

        {/* Formulaire d'upload de fichier preuve */}
        {showProofUpload && (
          <div style={styles.formContainer}>
            <form onSubmit={handleProofUpload} style={styles.inputForm} encType="multipart/form-data">
              <input
                type="file"
                name="proof"
                accept="application/pdf,image/*"
                onChange={e => setProofFile(e.target.files[0])}
                style={{ flex: 1 }}
                required
              />
              <button
                type="submit"
                disabled={loading}
                style={styles.sendButton}
              >
                {loading ? (
                  <div style={styles.spinner}></div>
                ) : (
                  'Uploader la preuve'
                )}
              </button>
            </form>
            {proofUploadMessage && (
              <div style={{ marginTop: 8, color: '#6b7280' }}>{proofUploadMessage}</div>
            )}
          </div>
        )}

        {/* Zone de saisie (toujours en bas) */}
        {user && (
        <div style={styles.inputArea}>
          <form onSubmit={handleSubmit} style={styles.inputForm}>
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Tapez votre message..."
              style={styles.inputField}
              required
            />
            <button
              type="submit"
              disabled={loading}
              style={styles.sendButton}
            >
              {loading ? (
                <div style={styles.spinner}></div>
              ) : (
                'Envoyer'
              )}
            </button>
          </form>
        </div>
        )}
      </div>

      {/* Affichage du bouton RH si user.department === 'RH' */}
      {user && user.department && user.department.toUpperCase() === 'RH' && (
        <button
          style={{ ...styles.navButton, background: '#f3f4f6', color: '#3730a3', border: '1px solid #e5e7eb', position: 'fixed', bottom: '1rem', right: '1rem', zIndex: 200 }}
          onClick={() => setShowRHPanel(true)}
        >
          Liste demandes de congé
        </button>
      )}

      {/* RH Panel (modale ou panneau latéral) */}
      {showRHPanel && (
        <RHPanel user={user} onClose={() => setShowRHPanel(false)} />
      )}

      {/* Styles CSS */}
      <style jsx>{`
  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .spinner {
    width: 1rem;
    height: 1rem;
    border: 2px solid #fff;
    border-top: 2px solid transparent;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
`}</style>
    </div>
  );
}

// Styles CSS
const styles = {
  navbarGlobal: {
    width: '100%',
    maxWidth: '100vw',
    position: 'fixed',
    top: 0,
    left: 0,
    zIndex: 10000, // Augmenté pour s'assurer que la navbar est au-dessus des autres éléments
    background: '#fff',
    boxShadow: '0 2px 4px rgba(0,0,0,0.04)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    padding: '0.5rem 2rem',
    minHeight: 56,
    borderRadius: 0,
    boxSizing: 'border-box',
    flexWrap: 'nowrap',
    overflow: 'hidden',
    gap: 16,
  },
  navButton: {
    background: '#e0e7ff',
    color: '#3730a3',
    border: 'none',
    borderRadius: 8,
    padding: '0.5rem 1rem',
    fontWeight: 600,
    cursor: 'pointer',
    fontSize: '0.95rem',
    maxWidth: 160,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(to bottom right, #f0f4ff, #f9f0ff)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1rem',
    flexDirection: 'column', // Pour que le navbar soit au-dessus
    paddingTop: 72, // Décaler le contenu sous la navbar fixe
  },
  chatContainer: {
    width: '100%',
    maxWidth: '800px',
    background: '#fff',
    borderRadius: '12px',
    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
    display: 'flex',
    flexDirection: 'column',
    height: '80vh',
    overflow: 'hidden',
  },
  header: {
    background: 'linear-gradient(to right, #3b82f6, #8b5cf6)',
    padding: '1.5rem',
    color: '#fff',
  },
  headerTitle: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    margin: 0,
  },
  headerSubtitle: {
    fontSize: '0.875rem',
    margin: 0,
    opacity: 0.8,
  },
  chatArea: {
    flex: 1,
    padding: '1.5rem',
    overflowY: 'auto',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  messageContainer: {
    display: 'flex',
  },
  messageBubble: {
    maxWidth: '75%',
    padding: '0.75rem 1rem',
    borderRadius: '12px',
  },
  messageText: {
    margin: 0,
    fontSize: '0.875rem',
    whiteSpace: 'pre-line',
  },
  inputArea: {
    borderTop: '1px solid #e5e7eb',
    padding: '1rem',
    background: '#f9fafb',
  },
  inputForm: {
    display: 'flex',
    gap: '0.5rem',
  },
  inputField: {
    flex: 1, // Prend tout l'espace disponible
    minWidth: 0,
    maxWidth: '100%',
    padding: '0.5rem 0.75rem',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    outline: 'none',
    fontSize: '0.95rem',
    boxSizing: 'border-box',
  },
  sendButton: {
    padding: '0.5rem 1rem',
    background: '#3b82f6',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontSize: '0.95rem',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    maxWidth: 120,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  userBlock: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    maxWidth: 220,
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
  },
  userName: {
    fontWeight: 500,
    color: '#3730a3',
    maxWidth: 120,
    overflow: 'hidden',
    whiteSpace: 'nowrap',
    textOverflow: 'ellipsis',
    fontSize: '0.95rem',
  },
  // ...autres styles existants...
  // Responsive
};

// Ajout d'un style global responsive
<style jsx global>{`
  @media (max-width: 600px) {
    nav {
      padding: 0.5rem 0.5rem !important;
    }
    .navbarGlobal {
      padding: 0.5rem 0.5rem !important;
    }
    input, button {
      font-size: 0.85rem !important;
      padding: 0.4rem 0.5rem !important;
    }
    .userName {
      max-width: 80px !important;
    }
  }
`}</style>
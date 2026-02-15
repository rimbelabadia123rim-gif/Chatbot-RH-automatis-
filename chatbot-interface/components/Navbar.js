import Image from 'next/image';
import { useState, useEffect, useRef } from 'react';

export default function Navbar({
  user,
  loginMatricule,
  setLoginMatricule,
  handleLogin,
  loading,
  loginError,
  handleLogout,
  handleNewChat,
  styles,
  onHistoryClick
}) {
  const [notificationCount, setNotificationCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const notificationRef = useRef(null);

  // Récupérer le nombre de notifications non lues
  useEffect(() => {
    if (user?.matricule) {
      fetchNotificationCount();
      // Actualiser toutes les 30 secondes
      const interval = setInterval(fetchNotificationCount, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  // Gestionnaire pour fermer le panel quand on clique ailleurs
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };

    if (showNotifications) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showNotifications]);

  const fetchNotificationCount = async () => {
    if (!user?.matricule) return;
    try {
      const response = await fetch(`/api/notifications-count?matricule=${user.matricule}`);
      const data = await response.json();
      setNotificationCount(data.unread_count || 0);
    } catch (error) {
      console.error('Erreur lors de la récupération du compteur:', error);
    }
  };

  const fetchNotifications = async () => {
    if (!user?.matricule) return;
    try {
      console.log('Fetching notifications for:', user.matricule);
      const response = await fetch(`/api/notifications?matricule=${user.matricule}`);
      const data = await response.json();
      console.log('Notifications response:', data);
      setNotifications(data.notifications || []);
    } catch (error) {
      console.error('Erreur lors de la récupération des notifications:', error);
    }
  };

  const handleNotificationClick = async () => {
    console.log('Notification clicked, current state:', showNotifications);
    console.log('User:', user);
    console.log('Notifications:', notifications);
    
    if (!showNotifications) {
      await fetchNotifications();
    }
    setShowNotifications(!showNotifications);
    console.log('New notification state:', !showNotifications);
  };

  const markAllAsRead = async () => {
    if (!user?.matricule) return;
    try {
      await fetch(`/api/notifications?matricule=${user.matricule}`, {
        method: 'POST'
      });
      setNotificationCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (error) {
      console.error('Erreur lors de la mise à jour:', error);
    }
  };

  return (
    <nav style={styles.navbarGlobal}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <Image src="/logo.png" alt="Logo" width={38} height={38} style={{ borderRadius: 8, background: '#fff' }} />
        <button
          onClick={handleNewChat}
          style={styles.navButton}
        >
          Nouveau chat
        </button>
      </div>
      <div style={{ flex: 1 }} />
      
      {/* Système de notifications - visible seulement si connecté */}
      {user && (
        <div ref={notificationRef} style={{ 
          position: 'relative', 
          marginRight: 16,
          zIndex: 10000 // Assurer que le conteneur parent a un z-index élevé
        }}>
          <Image 
            src="/notif.png" 
            alt="Notifications" 
            width={24} 
            height={24} 
            style={{ 
              cursor: 'pointer', 
              opacity: 0.7,
              transition: 'opacity 0.2s'
            }}
            onMouseOver={(e) => e.target.style.opacity = 1}
            onMouseOut={(e) => e.target.style.opacity = 0.7}
            onClick={handleNotificationClick}
          />
          
          {/* Badge avec le nombre de notifications */}
          {notificationCount > 0 && (
            <div style={{
              position: 'absolute',
              top: -8,
              right: -8,
              background: '#ef4444',
              color: '#fff',
              borderRadius: '50%',
              minWidth: 16,
              height: 16,
              fontSize: '0.7rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              zIndex: 10001
            }}>
              {notificationCount > 9 ? '9+' : notificationCount}
            </div>
          )}
          
          {/* Panel des notifications */}
          {showNotifications && (
            <div style={{
              position: 'fixed', // Changé de 'absolute' à 'fixed' pour éviter les problèmes de contexte de pile
              top: 60, // Position fixe depuis le haut de la fenêtre
              right: 20, // Position fixe depuis la droite
              background: '#fff',
              border: '2px solid #3b82f6',
              borderRadius: 8,
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
              width: 320,
              maxHeight: 400,
              overflow: 'hidden',
              zIndex: 99999 // Z-index très élevé pour passer au-dessus de tout
            }}>
              <div style={{
                padding: '12px 16px',
                borderBottom: '1px solid #e5e7eb',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: '#f9fafb'
              }}>
                <h3 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>
                  Notifications
                </h3>
                {notifications.some(n => !n.is_read) && (
                  <button
                    onClick={markAllAsRead}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#3b82f6',
                      fontSize: '0.8rem',
                      cursor: 'pointer',
                      textDecoration: 'underline'
                    }}
                  >
                    Tout marquer comme lu
                  </button>
                )}
              </div>
              
              <div style={{ maxHeight: 320, overflowY: 'auto' }}>
                {notifications.length === 0 ? (
                  <div style={{
                    padding: 24,
                    textAlign: 'center',
                    color: '#6b7280',
                    fontSize: '0.9rem'
                  }}>
                    Aucune notification
                  </div>
                ) : (
                  notifications.map((notification, index) => (
                    <div
                      key={index}
                      style={{
                        padding: '12px 16px',
                        borderBottom: index < notifications.length - 1 ? '1px solid #f3f4f6' : 'none',
                        background: notification.is_read ? '#fff' : '#f0f9ff',
                        cursor: 'pointer'
                      }}
                    >
                      <div style={{
                        fontWeight: notification.is_read ? 'normal' : '600',
                        fontSize: '0.85rem',
                        marginBottom: 4,
                        color: '#111827'
                      }}>
                        {notification.title}
                      </div>
                      <div style={{
                        fontSize: '0.8rem',
                        color: '#6b7280',
                        marginBottom: 4
                      }}>
                        {notification.message}
                      </div>
                      <div style={{
                        fontSize: '0.75rem',
                        color: '#9ca3af'
                      }}>
                        {new Date(notification.created_at).toLocaleString('fr-FR')}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      )}
      
      {!user ? (
        <form onSubmit={handleLogin} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input
            type="text"
            value={loginMatricule}
            onChange={e => setLoginMatricule(e.target.value)}
            placeholder="Votre matricule"
            style={styles.inputField}
            required
          />
          <button type="submit" style={styles.sendButton} disabled={loading}>
            {loading ? <div style={styles.spinner}></div> : 'Connexion'}
          </button>
          {loginError && <span style={{ color: 'red', marginLeft: 8 }}>{loginError}</span>}
        </form>
      ) : (
        <div style={styles.userBlock}>
          <span style={styles.userName}>{user.first_name} {user.last_name}</span>
          <button onClick={handleLogout} style={{ ...styles.navButton, background: '#fee2e2', color: '#b91c1c' }}>Logout</button>
        </div>
      )}
    </nav>
  );
}

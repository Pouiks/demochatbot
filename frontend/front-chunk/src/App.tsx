import { useState } from 'react';
import SemanticSearch from './components/SemanticSearch';
import { AdminPanelEnhanced } from './pages/AdminPanelEnhanced';
import './App.css';

function App() {
  const [view, setView] = useState<'chat' | 'admin'>('chat');

  return (
    <>
      {view === 'chat' && (
        <>
          <button
            className="admin-nav-btn"
            onClick={() => setView('admin')}
            title="Accéder à l'administration"
          >
            Admin
          </button>
          <SemanticSearch />
        </>
      )}

      {view === 'admin' && (
        <>
          <button
            className="chat-nav-btn"
            onClick={() => setView('chat')}
            title="Retour au chat"
          >
            Retour au chat
          </button>
          <AdminPanelEnhanced />
        </>
      )}
    </>
  );
}

export default App

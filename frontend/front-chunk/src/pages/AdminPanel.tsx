import { useState, useEffect } from 'react';
import '../styles/AdminPanel.css';

const ADMIN_API_URL = import.meta.env.VITE_ADMIN_API_URL || 'http://localhost:8001';

interface Document {
    id: string;
    content: string;
    url: string;
    type: string;
    timestamp?: string;
}

interface Apartment {
    id: string;
    metadata: {
        city: string;
        rooms: number;
        rent_cc_eur: number;
        surface_m2: number;
        furnished: boolean;
        availability_date: string;
        energy_label?: string;
        postal_code?: string;
    };
}

interface Status {
    in_progress: boolean;
    last_update: string | null;
    documents_count: number;
    apartments_count: number;
    last_action: string | null;
}

export function AdminPanel() {
    const [activeTab, setActiveTab] = useState<'documents' | 'apartments'>('documents');
    const [status, setStatus] = useState<Status>({
        in_progress: false,
        last_update: null,
        documents_count: 0,
        apartments_count: 0,
        last_action: null
    });

    // Documents
    const [documents, setDocuments] = useState<Document[]>([]);
    const [newDoc, setNewDoc] = useState({ content: '', url: '', category: 'service' });

    // Apartments
    const [apartments, setApartments] = useState<Apartment[]>([]);
    const [newApt, setNewApt] = useState({
        city: 'Massy Palaiseau',
        rooms: 1,
        rent_cc_eur: 450,
        surface_m2: 20,
        furnished: true,
        availability_date: '',
        energy_label: 'C',
        postal_code: ''
    });

    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    // Charger le statut toutes les 2 secondes
    useEffect(() => {
        loadStatus();
        const interval = setInterval(loadStatus, 2000);
        return () => clearInterval(interval);
    }, []);

    // Charger les documents et appartements au montage
    useEffect(() => {
        loadDocuments();
        loadApartments();
    }, []);

    const loadStatus = async () => {
        try {
            const response = await fetch(`${ADMIN_API_URL}/admin/status`);
            const data = await response.json();
            setStatus(data);
        } catch (error) {
            console.error('Erreur chargement statut:', error);
        }
    };

    const loadDocuments = async () => {
        try {
            const response = await fetch(`${ADMIN_API_URL}/admin/documents`);
            const data = await response.json();
            setDocuments(data);
        } catch (error) {
            console.error('Erreur chargement documents:', error);
        }
    };

    const loadApartments = async () => {
        try {
            const response = await fetch(`${ADMIN_API_URL}/admin/apartments`);
            const data = await response.json();
            setApartments(data);
        } catch (error) {
            console.error('Erreur chargement appartements:', error);
        }
    };

    const showMessage = (type: 'success' | 'error', text: string) => {
        setMessage({ type, text });
        setTimeout(() => setMessage(null), 5000);
    };

    // === GESTION DOCUMENTS ===

    const handleAddDocument = async () => {
        if (!newDoc.content || newDoc.content.length < 10) {
            showMessage('error', 'Le contenu doit contenir au moins 10 caractères');
            return;
        }

        try {
            const response = await fetch(`${ADMIN_API_URL}/admin/documents`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newDoc)
            });

            const data = await response.json();

            if (response.ok) {
                showMessage('success', data.message);
                setNewDoc({ content: '', url: '', category: 'service' });
                loadDocuments();
            } else {
                showMessage('error', data.detail || 'Erreur lors de l\'ajout');
            }
        } catch (error) {
            showMessage('error', 'Erreur réseau');
        }
    };

    const handleDeleteDocument = async (id: string) => {
        if (!confirm('Supprimer ce document ?')) return;

        try {
            const response = await fetch(`${ADMIN_API_URL}/admin/documents/${id}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok) {
                showMessage('success', data.message);
                loadDocuments();
            } else {
                showMessage('error', data.detail || 'Erreur lors de la suppression');
            }
        } catch (error) {
            showMessage('error', 'Erreur réseau');
        }
    };

    // === GESTION APPARTEMENTS ===

    const handleAddApartment = async () => {
        if (newApt.rent_cc_eur <= 0 || newApt.surface_m2 <= 0) {
            showMessage('error', 'Valeurs invalides');
            return;
        }

        try {
            const response = await fetch(`${ADMIN_API_URL}/admin/apartments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newApt)
            });

            const data = await response.json();

            if (response.ok) {
                showMessage('success', data.message);
                setNewApt({
                    city: 'Massy Palaiseau',
                    rooms: 1,
                    rent_cc_eur: 450,
                    surface_m2: 20,
                    furnished: true,
                    availability_date: '',
                    energy_label: 'C',
                    postal_code: ''
                });
                loadApartments();
            } else {
                showMessage('error', data.detail || 'Erreur lors de l\'ajout');
            }
        } catch (error) {
            showMessage('error', 'Erreur réseau');
        }
    };

    const handleDeleteApartment = async (id: string) => {
        if (!confirm('Supprimer cet appartement ?')) return;

        try {
            const response = await fetch(`${ADMIN_API_URL}/admin/apartments/${id}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (response.ok) {
                showMessage('success', data.message);
                loadApartments();
            } else {
                showMessage('error', data.detail || 'Erreur lors de la suppression');
            }
        } catch (error) {
            showMessage('error', 'Erreur réseau');
        }
    };

    const handleUploadJSON = async () => {
        if (!uploadFile) {
            showMessage('error', 'Sélectionnez un fichier JSON');
            return;
        }

        const formData = new FormData();
        formData.append('file', uploadFile);

        try {
            const response = await fetch(`${ADMIN_API_URL}/admin/apartments/upload`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                showMessage('success', data.message);
                setUploadFile(null);
                loadApartments();
            } else {
                showMessage('error', data.detail || 'Erreur lors de l\'import');
            }
        } catch (error) {
            showMessage('error', 'Erreur réseau');
        }
    };

    const handleReindexAll = async () => {
        if (!confirm('Ré-indexer toutes les données ?')) return;

        try {
            const response = await fetch(`${ADMIN_API_URL}/admin/reindex-all`, {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                showMessage('success', data.message);
            } else {
                showMessage('error', 'Erreur lors de la ré-indexation');
            }
        } catch (error) {
            showMessage('error', 'Erreur réseau');
        }
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return 'Jamais';
        const date = new Date(dateStr);
        return date.toLocaleString('fr-FR');
    };

    return (
        <div className="admin-panel">
            <header className="admin-header">
                <h1>🏠 ECLA - Administration</h1>

                {status.in_progress && (
                    <div className="indexing-banner">
                        <div className="spinner"></div>
                        <span>🔄 {status.last_action || 'Ré-indexation en cours...'}</span>
                    </div>
                )}

                {!status.in_progress && status.last_update && (
                    <div className="sync-status">
                        ✅ Dernière synchronisation : {formatDate(status.last_update)}
                    </div>
                )}
            </header>

            {message && (
                <div className={`message ${message.type}`}>
                    {message.text}
                </div>
            )}

            <div className="admin-stats">
                <div className="stat-card">
                    <span className="stat-icon">📚</span>
                    <span className="stat-label">Documents</span>
                    <span className="stat-value">{status.documents_count}</span>
                </div>
                <div className="stat-card">
                    <span className="stat-icon">🏢</span>
                    <span className="stat-label">Appartements</span>
                    <span className="stat-value">{status.apartments_count}</span>
                </div>
                <button className="reindex-btn" onClick={handleReindexAll}>
                    🔄 Tout ré-indexer
                </button>
            </div>

            <div className="admin-tabs">
                <button
                    className={activeTab === 'documents' ? 'active' : ''}
                    onClick={() => setActiveTab('documents')}
                >
                    📚 Documentation
                </button>
                <button
                    className={activeTab === 'apartments' ? 'active' : ''}
                    onClick={() => setActiveTab('apartments')}
                >
                    🏢 Appartements
                </button>
            </div>

            <div className="admin-content">
                {activeTab === 'documents' && (
                    <div className="documents-section">
                        <div className="add-form">
                            <h2>➕ Ajouter de la documentation</h2>

                            <label>
                                Type de contenu :
                                <select
                                    value={newDoc.category}
                                    onChange={(e) => setNewDoc({ ...newDoc, category: e.target.value })}
                                >
                                    <option value="service">Services ECLA</option>
                                    <option value="faq">FAQ</option>
                                    <option value="partnership">Partenariats</option>
                                    <option value="procedure">Procédure de réservation</option>
                                    <option value="other">Autre</option>
                                </select>
                            </label>

                            <label>
                                Contenu :
                                <textarea
                                    value={newDoc.content}
                                    onChange={(e) => setNewDoc({ ...newDoc, content: e.target.value })}
                                    placeholder="Écrivez le contenu de la documentation..."
                                    rows={6}
                                />
                            </label>

                            <label>
                                URL source (optionnel) :
                                <input
                                    type="text"
                                    value={newDoc.url}
                                    onChange={(e) => setNewDoc({ ...newDoc, url: e.target.value })}
                                    placeholder="https://ecla.com/services"
                                />
                            </label>

                            <button className="add-btn" onClick={handleAddDocument}>
                                ✅ Ajouter et indexer
                            </button>
                        </div>

                        <div className="items-list">
                            <h3>Documents actuels ({documents.length})</h3>
                            {documents.map((doc) => (
                                <div key={doc.id} className="item-card">
                                    <div className="item-header">
                                        <span className="item-type">{doc.type}</span>
                                        {doc.timestamp && (
                                            <span className="item-date">📅 {formatDate(doc.timestamp)}</span>
                                        )}
                                    </div>
                                    <div className="item-content">
                                        {doc.content.substring(0, 150)}...
                                    </div>
                                    {doc.url && (
                                        <div className="item-url">
                                            🔗 <a href={doc.url} target="_blank" rel="noopener noreferrer">{doc.url}</a>
                                        </div>
                                    )}
                                    <div className="item-actions">
                                        <button className="delete-btn" onClick={() => handleDeleteDocument(doc.id)}>
                                            🗑️ Supprimer
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {activeTab === 'apartments' && (
                    <div className="apartments-section">
                        <div className="add-form">
                            <h2>📦 Importer un fichier JSON</h2>
                            <div className="upload-zone">
                                <input
                                    type="file"
                                    accept=".json,.jsonl"
                                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                                />
                                {uploadFile && <span className="file-name">📄 {uploadFile.name}</span>}
                                <button className="upload-btn" onClick={handleUploadJSON}>
                                    🔄 Remplacer tous les appartements
                                </button>
                            </div>

                            <h2>➕ Ajouter un appartement manuellement</h2>

                            <div className="form-grid">
                                <label>
                                    Ville :
                                    <select
                                        value={newApt.city}
                                        onChange={(e) => setNewApt({ ...newApt, city: e.target.value })}
                                    >
                                        <option>Massy Palaiseau</option>
                                        <option>Noisy le grand</option>
                                        <option>Villejuif</option>
                                        <option>Archamps - Genève</option>
                                    </select>
                                </label>

                                <label>
                                    Type :
                                    <select
                                        value={newApt.rooms}
                                        onChange={(e) => setNewApt({ ...newApt, rooms: parseInt(e.target.value) })}
                                    >
                                        <option value="1">Studio (T1)</option>
                                        <option value="2">T2</option>
                                        <option value="3">T3</option>
                                    </select>
                                </label>

                                <label>
                                    Loyer CC (€) :
                                    <input
                                        type="number"
                                        value={newApt.rent_cc_eur}
                                        onChange={(e) => setNewApt({ ...newApt, rent_cc_eur: parseFloat(e.target.value) })}
                                    />
                                </label>

                                <label>
                                    Surface (m²) :
                                    <input
                                        type="number"
                                        value={newApt.surface_m2}
                                        onChange={(e) => setNewApt({ ...newApt, surface_m2: parseFloat(e.target.value) })}
                                    />
                                </label>

                                <label>
                                    Meublé :
                                    <input
                                        type="checkbox"
                                        checked={newApt.furnished}
                                        onChange={(e) => setNewApt({ ...newApt, furnished: e.target.checked })}
                                    />
                                </label>

                                <label>
                                    Disponible le :
                                    <input
                                        type="date"
                                        value={newApt.availability_date}
                                        onChange={(e) => setNewApt({ ...newApt, availability_date: e.target.value })}
                                    />
                                </label>
                            </div>

                            <button className="add-btn" onClick={handleAddApartment}>
                                ✅ Ajouter
                            </button>
                        </div>

                        <div className="items-list">
                            <h3>Appartements actuels ({apartments.length})</h3>
                            {apartments.map((apt) => (
                                <div key={apt.id} className="item-card">
                                    <div className="apartment-info">
                                        <h4>🏠 {apt.metadata.city} - T{apt.metadata.rooms}</h4>
                                        <p>
                                            💰 {apt.metadata.rent_cc_eur}€ |
                                            📐 {apt.metadata.surface_m2}m² |
                                            {apt.metadata.furnished ? '🛋️ Meublé' : '📦 Non meublé'} |
                                            📅 {apt.metadata.availability_date}
                                        </p>
                                        <p className="apt-id">ID: {apt.id}</p>
                                    </div>
                                    <div className="item-actions">
                                        <button className="delete-btn" onClick={() => handleDeleteApartment(apt.id)}>
                                            🗑️ Supprimer
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}


import { useState, useEffect } from 'react';

interface ApartmentOptions {
    floorChoice: 'any' | 'low' | 'medium' | 'high';
    orientationChoice: 'any' | 'north' | 'south' | 'east' | 'west';
    bedChoice: 'any' | '140' | '160' | '180';
    acChoice: 'any' | 'with' | 'without';
}

interface ServiceOptions {
    tv: boolean;
    packLinge: boolean;
    parkingIndoor: boolean;
    parkingOutdoor: boolean;
}

interface Apartment {
    id: string;
    typologie_id?: string;
    city: string;
    rooms: number;
    surface_m2: number;
    furnished: boolean;
    rent_cc_eur: number;
    availability_date: string;
    energy_label: string;
    postal_code: string;
    floor?: number;
    orientation?: string;
    bed_size?: number;
    has_ac?: boolean;
    application_fee?: number;
    deposit_months?: number;
    is_typologie?: boolean;
    content: string;
}

interface UpsellOptionsModalProps {
    typologie: Apartment;
    currentOptions: ServiceOptions;
    onValidate: (options: ServiceOptions, total: number) => void;
    onClose: () => void;
}

const calculateFloorSupplement = (floorChoice: string): number => {
    switch (floorChoice) {
        case 'low': return 30;
        case 'medium': return 50;
        case 'high': return 80;
        default: return 0;
    }
};

const calculateBedSupplement = (bedChoice: string): number => {
    switch (bedChoice) {
        case '160': return 20;
        case '180': return 40;
        default: return 0;
    }
};

const calculateAcSupplement = (acChoice: string): number => {
    return acChoice === 'with' ? 50 : 0;
};

const calculateServicesCost = (options: ServiceOptions): number => {
    let cost = 0;
    if (options.tv) cost += 40;
    if (options.packLinge) cost += 30;
    if (options.parkingIndoor) cost += 50;
    if (options.parkingOutdoor) cost += 30;
    return cost;
};

export default function UpsellOptionsModal({ typologie, currentOptions, onValidate, onClose }: UpsellOptionsModalProps) {
    console.log('[UpsellOptionsModal] Modal rendered for typologie:', typologie.id);

    const [currentStep, setCurrentStep] = useState(1);
    const [isFooterExpanded, setIsFooterExpanded] = useState(false);

    // Options de l'appartement (Étape 1)
    const [apartmentOptions, setApartmentOptions] = useState<ApartmentOptions>({
        floorChoice: 'any',
        orientationChoice: 'any',
        bedChoice: 'any',
        acChoice: 'any'
    });

    // Services supplémentaires (Étape 2)
    const [serviceOptions, setServiceOptions] = useState<ServiceOptions>(currentOptions);

    // Calculs des suppléments
    const floorSupplement = calculateFloorSupplement(apartmentOptions.floorChoice);
    const bedSupplement = calculateBedSupplement(apartmentOptions.bedChoice);
    const acSupplement = calculateAcSupplement(apartmentOptions.acChoice);
    const apartmentSupplementsTotal = floorSupplement + bedSupplement + acSupplement;

    const servicesCost = calculateServicesCost(serviceOptions);
    const totalRent = typologie.rent_cc_eur + apartmentSupplementsTotal + servicesCost;

    // Calculer les frais initiaux
    const applicationFee = typologie.application_fee || 100;
    const depositAmount = totalRent * (typologie.deposit_months || 1);

    const toggleService = (service: keyof ServiceOptions) => {
        setServiceOptions(prev => ({
            ...prev,
            [service]: !prev[service]
        }));
    };

    const handleValidate = () => {
        onValidate(serviceOptions, totalRent);
    };

    const goToNextStep = () => {
        setCurrentStep(2);
        setIsFooterExpanded(false);
    };

    const goToPreviousStep = () => {
        setCurrentStep(1);
        setIsFooterExpanded(false);
    };

    // Empêcher le scroll du body quand le modal est ouvert
    useEffect(() => {
        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, []);

    return (
        <div className="upsell-modal-overlay" onClick={onClose}>
            <div className="upsell-modal" onClick={(e) => e.stopPropagation()}>
                <div className="upsell-modal-header">
                    <h2>Personnalisez votre logement</h2>
                    <button className="upsell-modal-close" onClick={onClose}>×</button>
                </div>

                {/* Progress bar */}
                <div className="upsell-progress-bar">
                    <div className="progress-steps">
                        <div className={`progress-step ${currentStep >= 1 ? 'active' : ''}`}>
                            <div className="step-number">1</div>
                            <div className="step-label">Appartement</div>
                        </div>
                        <div className="progress-line"></div>
                        <div className={`progress-step ${currentStep >= 2 ? 'active' : ''}`}>
                            <div className="step-number">2</div>
                            <div className="step-label">Services</div>
                        </div>
                    </div>
                </div>

                <div className="upsell-modal-body">
                    <div className="upsell-summary">
                        <h3>{typologie.rooms === 0 ? 'Colocation' : `T${typologie.rooms}`} - {typologie.surface_m2}m² à {typologie.city}</h3>
                        <p className="upsell-base-price">Loyer de base : {typologie.rent_cc_eur}€/mois</p>
                    </div>

                    {/* ÉTAPE 1 : Options de l'appartement */}
                    {currentStep === 1 && (
                        <div className="upsell-step-content">
                            {/* Choix de l'étage */}
                            <div className="option-group">
                                <h4 className="option-group-title">Choix de l'étage</h4>
                                <div className="option-buttons-grid">
                                    <button
                                        className={`option-btn ${apartmentOptions.floorChoice === 'any' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, floorChoice: 'any' }))}
                                    >
                                        <span className="option-icon">🎲</span>
                                        <span className="option-label">Peu importe</span>
                                        <span className="option-price">Prix de base</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.floorChoice === 'low' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, floorChoice: 'low' }))}
                                    >
                                        <span className="option-icon">🏢</span>
                                        <span className="option-label">Étage bas (0-2)</span>
                                        <span className="option-price">+30€/mois</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.floorChoice === 'medium' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, floorChoice: 'medium' }))}
                                    >
                                        <span className="option-icon">🏢</span>
                                        <span className="option-label">Étage moyen (3-4)</span>
                                        <span className="option-price">+50€/mois</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.floorChoice === 'high' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, floorChoice: 'high' }))}
                                    >
                                        <span className="option-icon">🏢</span>
                                        <span className="option-label">Étage haut (5+)</span>
                                        <span className="option-price">+80€/mois</span>
                                    </button>
                                </div>
                            </div>

                            {/* Choix de l'orientation */}
                            <div className="option-group">
                                <h4 className="option-group-title">Orientation</h4>
                                <div className="option-buttons-grid">
                                    <button
                                        className={`option-btn ${apartmentOptions.orientationChoice === 'any' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, orientationChoice: 'any' }))}
                                    >
                                        <span className="option-icon">🎲</span>
                                        <span className="option-label">Peu importe</span>
                                        <span className="option-price">Prix de base</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.orientationChoice === 'north' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, orientationChoice: 'north' }))}
                                    >
                                        <span className="option-icon">🧭</span>
                                        <span className="option-label">Nord</span>
                                        <span className="option-price">Inclus</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.orientationChoice === 'south' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, orientationChoice: 'south' }))}
                                    >
                                        <span className="option-icon">☀️</span>
                                        <span className="option-label">Sud</span>
                                        <span className="option-price">Inclus</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.orientationChoice === 'east' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, orientationChoice: 'east' }))}
                                    >
                                        <span className="option-icon">🌅</span>
                                        <span className="option-label">Est</span>
                                        <span className="option-price">Inclus</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.orientationChoice === 'west' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, orientationChoice: 'west' }))}
                                    >
                                        <span className="option-icon">🌇</span>
                                        <span className="option-label">Ouest</span>
                                        <span className="option-price">Inclus</span>
                                    </button>
                                </div>
                            </div>

                            {/* Taille du lit */}
                            <div className="option-group">
                                <h4 className="option-group-title">Taille du lit</h4>
                                <div className="option-buttons-grid">
                                    <button
                                        className={`option-btn ${apartmentOptions.bedChoice === 'any' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, bedChoice: 'any' }))}
                                    >
                                        <span className="option-icon">🎲</span>
                                        <span className="option-label">Peu importe</span>
                                        <span className="option-price">Prix de base</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.bedChoice === '140' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, bedChoice: '140' }))}
                                    >
                                        <span className="option-icon">🛏️</span>
                                        <span className="option-label">Lit 140cm</span>
                                        <span className="option-price">Inclus</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.bedChoice === '160' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, bedChoice: '160' }))}
                                    >
                                        <span className="option-icon">🛏️</span>
                                        <span className="option-label">Lit 160cm</span>
                                        <span className="option-price">+20€/mois</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.bedChoice === '180' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, bedChoice: '180' }))}
                                    >
                                        <span className="option-icon">🛏️</span>
                                        <span className="option-label">Lit 180cm</span>
                                        <span className="option-price">+40€/mois</span>
                                    </button>
                                </div>
                            </div>

                            {/* Climatisation */}
                            <div className="option-group">
                                <h4 className="option-group-title">Climatisation</h4>
                                <div className="option-buttons-grid">
                                    <button
                                        className={`option-btn ${apartmentOptions.acChoice === 'any' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, acChoice: 'any' }))}
                                    >
                                        <span className="option-icon">🎲</span>
                                        <span className="option-label">Peu importe</span>
                                        <span className="option-price">Prix de base</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.acChoice === 'with' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, acChoice: 'with' }))}
                                    >
                                        <span className="option-icon">❄️</span>
                                        <span className="option-label">Avec climatisation</span>
                                        <span className="option-price">+50€/mois</span>
                                    </button>
                                    <button
                                        className={`option-btn ${apartmentOptions.acChoice === 'without' ? 'active' : ''}`}
                                        onClick={() => setApartmentOptions(prev => ({ ...prev, acChoice: 'without' }))}
                                    >
                                        <span className="option-icon">🌡️</span>
                                        <span className="option-label">Sans climatisation</span>
                                        <span className="option-price">Inclus</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ÉTAPE 2 : Services supplémentaires */}
                    {currentStep === 2 && (
                        <div className="upsell-step-content">
                            <h4 className="step-title">Services supplémentaires</h4>

                            <label className="upsell-option">
                                <div className="upsell-option-info">
                                    <input
                                        type="checkbox"
                                        checked={serviceOptions.tv}
                                        onChange={() => toggleService('tv')}
                                    />
                                    <div>
                                        <span className="upsell-option-name">📺 Télévision</span>
                                        <span className="upsell-option-desc">TV écran plat avec chaînes incluses</span>
                                    </div>
                                </div>
                                <span className="upsell-option-price">+40€/mois</span>
                            </label>

                            <label className="upsell-option">
                                <div className="upsell-option-info">
                                    <input
                                        type="checkbox"
                                        checked={serviceOptions.packLinge}
                                        onChange={() => toggleService('packLinge')}
                                    />
                                    <div>
                                        <span className="upsell-option-name">🛏️ Pack linge</span>
                                        <span className="upsell-option-desc">Draps, couettes et serviettes fournis</span>
                                    </div>
                                </div>
                                <span className="upsell-option-price">+30€/mois</span>
                            </label>

                            <label className="upsell-option">
                                <div className="upsell-option-info">
                                    <input
                                        type="checkbox"
                                        checked={serviceOptions.parkingIndoor}
                                        onChange={() => toggleService('parkingIndoor')}
                                        disabled={serviceOptions.parkingOutdoor}
                                    />
                                    <div>
                                        <span className="upsell-option-name">🅿️ Place de parking sous-sol</span>
                                        <span className="upsell-option-desc">Parking sécurisé en sous-sol</span>
                                    </div>
                                </div>
                                <span className="upsell-option-price">+50€/mois</span>
                            </label>

                            <label className="upsell-option">
                                <div className="upsell-option-info">
                                    <input
                                        type="checkbox"
                                        checked={serviceOptions.parkingOutdoor}
                                        onChange={() => toggleService('parkingOutdoor')}
                                        disabled={serviceOptions.parkingIndoor}
                                    />
                                    <div>
                                        <span className="upsell-option-name">🅿️ Place de parking extérieur</span>
                                        <span className="upsell-option-desc">Parking extérieur surveillé</span>
                                    </div>
                                </div>
                                <span className="upsell-option-price">+30€/mois</span>
                            </label>
                        </div>
                    )}
                </div>

                <div className={`upsell-modal-footer-sticky ${isFooterExpanded ? 'expanded' : ''}`}>
                    {/* Toggle button */}
                    <button
                        className="upsell-footer-toggle"
                        onClick={() => setIsFooterExpanded(!isFooterExpanded)}
                        aria-label={isFooterExpanded ? "Réduire les détails" : "Voir les détails"}
                    >
                        <span className="toggle-arrow">{isFooterExpanded ? '▼' : '▲'}</span>
                    </button>

                    {/* Contenu scrollable déplié */}
                    {isFooterExpanded && (
                        <div className="upsell-footer-details-expanded">
                            {/* Section Loyer de base + Options appartement */}
                            <div className="upsell-footer-section upsell-footer-rent">
                                <div className="upsell-footer-line upsell-footer-main">
                                    <span className="upsell-footer-label">Loyer de base</span>
                                    <span className="upsell-footer-value">{typologie.rent_cc_eur}€/mois</span>
                                </div>

                                {apartmentSupplementsTotal > 0 && (
                                    <>
                                        <div className="upsell-footer-extras-title">Options appartement</div>
                                        {floorSupplement > 0 && (
                                            <div className="upsell-footer-line upsell-footer-extra">
                                                <span>Étage {apartmentOptions.floorChoice}</span>
                                                <span>+{floorSupplement}€/mois</span>
                                            </div>
                                        )}
                                        {bedSupplement > 0 && (
                                            <div className="upsell-footer-line upsell-footer-extra">
                                                <span>Lit {apartmentOptions.bedChoice}cm</span>
                                                <span>+{bedSupplement}€/mois</span>
                                            </div>
                                        )}
                                        {acSupplement > 0 && (
                                            <div className="upsell-footer-line upsell-footer-extra">
                                                <span>Climatisation</span>
                                                <span>+{acSupplement}€/mois</span>
                                            </div>
                                        )}
                                    </>
                                )}
                            </div>

                            {/* Section Services */}
                            {servicesCost > 0 && (
                                <div className="upsell-footer-section upsell-footer-rent">
                                    <div className="upsell-footer-extras-title">Services supplémentaires</div>
                                    {serviceOptions.tv && (
                                        <div className="upsell-footer-line upsell-footer-extra">
                                            <span>Télévision</span>
                                            <span>+40€/mois</span>
                                        </div>
                                    )}
                                    {serviceOptions.packLinge && (
                                        <div className="upsell-footer-line upsell-footer-extra">
                                            <span>Pack linge</span>
                                            <span>+30€/mois</span>
                                        </div>
                                    )}
                                    {serviceOptions.parkingIndoor && (
                                        <div className="upsell-footer-line upsell-footer-extra">
                                            <span>Parking sous-sol</span>
                                            <span>+50€/mois</span>
                                        </div>
                                    )}
                                    {serviceOptions.parkingOutdoor && (
                                        <div className="upsell-footer-line upsell-footer-extra">
                                            <span>Parking extérieur</span>
                                            <span>+30€/mois</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Section Prix Total */}
                            <div className="upsell-footer-section upsell-footer-total-section">
                                <div className="upsell-footer-charges">Charges comprises</div>

                                <div className="upsell-footer-line upsell-footer-fees">
                                    <span>+ Frais de dossier</span>
                                    <span>{applicationFee}€</span>
                                </div>
                                <div className="upsell-footer-line upsell-footer-fees">
                                    <span>+ Dépôt de garantie</span>
                                    <span>{depositAmount}€</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Prix total toujours visible */}
                    <div className="upsell-footer-total-bar">
                        <div className="upsell-footer-total-line">
                            <span className="upsell-footer-label-total">Prix total</span>
                            <span className="upsell-footer-value-total">{totalRent}€/mois</span>
                        </div>
                    </div>

                    {/* Boutons de navigation */}
                    <div className="upsell-navigation-buttons">
                        {currentStep === 1 ? (
                            <button className="upsell-validate-btn upsell-next-btn" onClick={goToNextStep}>
                                Suivant
                            </button>
                        ) : (
                            <>
                                <button className="upsell-back-btn" onClick={goToPreviousStep}>
                                    ← Précédent
                                </button>
                                <button className="upsell-validate-btn" onClick={handleValidate}>
                                    Valider ma réservation
                                </button>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

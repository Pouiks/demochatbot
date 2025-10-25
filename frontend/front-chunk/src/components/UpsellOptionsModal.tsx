import { useState, useEffect } from 'react';

interface UpsellOptions {
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
    currentOptions: UpsellOptions;
    onValidate: (options: UpsellOptions, total: number) => void;
    onClose: () => void;
}

const calculateFloorSupplement = (floor: number): number => {
    if (floor === 0) return 0;
    if (floor <= 2) return 30;
    if (floor <= 4) return 50;
    if (floor <= 6) return 80;
    return 100;
};

const calculateOptionsCost = (options: UpsellOptions): number => {
    let cost = 0;
    if (options.tv) cost += 40;
    if (options.packLinge) cost += 30;
    if (options.parkingIndoor) cost += 50;
    if (options.parkingOutdoor) cost += 30;
    return cost;
};

export default function UpsellOptionsModal({ typologie, currentOptions, onValidate, onClose }: UpsellOptionsModalProps) {
    const [options, setOptions] = useState<UpsellOptions>(currentOptions);

    const floorSupplement = calculateFloorSupplement(typologie.floor || 0);
    const optionsCost = calculateOptionsCost(options);
    const totalRent = typologie.rent_cc_eur + floorSupplement + optionsCost;

    const toggleOption = (option: keyof UpsellOptions) => {
        setOptions(prev => ({
            ...prev,
            [option]: !prev[option]
        }));
    };

    const handleValidate = () => {
        onValidate(options, totalRent);
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

                <div className="upsell-modal-body">
                    <div className="upsell-summary">
                        <h3>{typologie.rooms === 0 ? 'Colocation' : `T${typologie.rooms}`} - {typologie.surface_m2}m² à {typologie.city}</h3>
                        <p className="upsell-floor-info">
                            Étage {typologie.floor} - Orientation {typologie.orientation}
                        </p>
                    </div>

                    <div className="upsell-price-breakdown">
                        <div className="upsell-price-line">
                            <span>Loyer de base</span>
                            <span>{typologie.rent_cc_eur}€/mois</span>
                        </div>
                        <div className="upsell-price-line upsell-supplement">
                            <span>Supplément étage {typologie.floor}</span>
                            <span>+{floorSupplement}€/mois</span>
                        </div>
                    </div>

                    <div className="upsell-options-section">
                        <h3>Options disponibles</h3>

                        <label className="upsell-option">
                            <div className="upsell-option-info">
                                <input
                                    type="checkbox"
                                    checked={options.tv}
                                    onChange={() => toggleOption('tv')}
                                />
                                <div>
                                    <span className="upsell-option-name">Télévision</span>
                                    <span className="upsell-option-desc">TV écran plat avec chaînes incluses</span>
                                </div>
                            </div>
                            <span className="upsell-option-price">+40€/mois</span>
                        </label>

                        <label className="upsell-option">
                            <div className="upsell-option-info">
                                <input
                                    type="checkbox"
                                    checked={options.packLinge}
                                    onChange={() => toggleOption('packLinge')}
                                />
                                <div>
                                    <span className="upsell-option-name">Pack linge</span>
                                    <span className="upsell-option-desc">Draps, couettes et serviettes fournis</span>
                                </div>
                            </div>
                            <span className="upsell-option-price">+30€/mois</span>
                        </label>

                        <label className="upsell-option">
                            <div className="upsell-option-info">
                                <input
                                    type="checkbox"
                                    checked={options.parkingIndoor}
                                    onChange={() => toggleOption('parkingIndoor')}
                                    disabled={options.parkingOutdoor}
                                />
                                <div>
                                    <span className="upsell-option-name">Place de parking sous-sol</span>
                                    <span className="upsell-option-desc">Parking sécurisé en sous-sol</span>
                                </div>
                            </div>
                            <span className="upsell-option-price">+50€/mois</span>
                        </label>

                        <label className="upsell-option">
                            <div className="upsell-option-info">
                                <input
                                    type="checkbox"
                                    checked={options.parkingOutdoor}
                                    onChange={() => toggleOption('parkingOutdoor')}
                                    disabled={options.parkingIndoor}
                                />
                                <div>
                                    <span className="upsell-option-name">Place de parking extérieur</span>
                                    <span className="upsell-option-desc">Parking extérieur surveillé</span>
                                </div>
                            </div>
                            <span className="upsell-option-price">+30€/mois</span>
                        </label>
                    </div>
                </div>

                <div className="upsell-modal-footer">
                    <div className="upsell-total">
                        <span>Total mensuel</span>
                        <span className="upsell-total-price">{totalRent}€/mois</span>
                    </div>
                    <button className="upsell-validate-btn" onClick={handleValidate}>
                        Valider mes options
                    </button>
                </div>
            </div>
        </div>
    );
}


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

interface BookingSummary {
    typologie: Apartment;
    baseRent: number;
    floorSupplement: number;
    optionsCost: number;
    totalRent: number;
    applicationFee: number;
    deposit: number;
    selectedOptions: string[];
}

interface BookingSummaryProps {
    summary: BookingSummary;
    onModifyOptions: () => void;
    onContinueChat: () => void;
    onFinalize: () => void;
}

export default function BookingSummary({ summary, onModifyOptions, onContinueChat, onFinalize }: BookingSummaryProps) {
    const { typologie, baseRent, floorSupplement, optionsCost, totalRent, applicationFee, deposit, selectedOptions } = summary;

    const typologieName = typologie.rooms === 0
        ? 'Colocation'
        : typologie.rooms === 1 && typologie.surface_m2 < 23
            ? 'Studio'
            : `T${typologie.rooms}`;

    return (
        <div className="booking-summary">
            <div className="booking-summary-header">
                <h3>📋 RÉCAPITULATIF DE VOTRE RÉSERVATION</h3>
            </div>

            <div className="booking-summary-body">
                <div className="booking-summary-section">
                    <h4>Logement</h4>
                    <p className="booking-summary-typologie">
                        {typologieName} {typologie.surface_m2}m² - {typologie.city}
                    </p>
                    <p className="booking-summary-details">
                        Étage {typologie.floor} - Orientation {typologie.orientation}
                    </p>
                    {typologie.bed_size && (
                        <p className="booking-summary-details">
                            Lit {typologie.bed_size}cm
                            {typologie.has_ac && ' - Climatisation'}
                        </p>
                    )}
                </div>

                <div className="booking-summary-section">
                    <h4>Détail du loyer mensuel</h4>
                    <div className="booking-summary-line">
                        <span>Loyer de base</span>
                        <span>{baseRent}€</span>
                    </div>
                    {floorSupplement > 0 && (
                        <div className="booking-summary-line booking-summary-supplement">
                            <span>Supplément étage</span>
                            <span>+{floorSupplement}€</span>
                        </div>
                    )}
                    {selectedOptions.length > 0 && (
                        <>
                            <div className="booking-summary-options-header">Options :</div>
                            {selectedOptions.map((option, idx) => (
                                <div key={idx} className="booking-summary-line booking-summary-option">
                                    <span>• {option}</span>
                                </div>
                            ))}
                            <div className="booking-summary-line booking-summary-supplement">
                                <span>Total options</span>
                                <span>+{optionsCost}€</span>
                            </div>
                        </>
                    )}
                    <div className="booking-summary-line booking-summary-total">
                        <span>TOTAL MENSUEL</span>
                        <span className="booking-summary-total-amount">{totalRent}€</span>
                    </div>
                </div>

                <div className="booking-summary-section">
                    <h4>Frais initiaux</h4>
                    <div className="booking-summary-line">
                        <span>Frais de dossier</span>
                        <span>{applicationFee}€</span>
                    </div>
                    <div className="booking-summary-line">
                        <span>Dépôt de garantie</span>
                        <span>{deposit}€ ({typologie.deposit_months} mois)</span>
                    </div>
                </div>
            </div>

            <div className="booking-summary-footer">
                <button className="booking-summary-btn booking-summary-btn-secondary" onClick={onModifyOptions}>
                    Modifier mes options
                </button>
                <button className="booking-summary-btn booking-summary-btn-secondary" onClick={onContinueChat}>
                    Continuer à discuter
                </button>
                <button className="booking-summary-btn booking-summary-btn-primary" onClick={onFinalize}>
                    Finaliser ma réservation
                </button>
            </div>
        </div>
    );
}


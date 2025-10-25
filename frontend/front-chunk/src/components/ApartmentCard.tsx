import { useState } from 'react';

interface ApartmentCardProps {
  apartment: {
    id: string;
    typologie_id?: string;
    city: string;
    rooms: number;
    surface_m2: number;
    surface_min?: number;
    surface_max?: number;
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
  };
  onReserve?: (apartment: ApartmentCardProps['apartment']) => void;
}

export default function ApartmentCard({ apartment, onReserve }: ApartmentCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "Non spécifié";
    const date = new Date(dateStr);
    return date.toLocaleDateString("fr-FR", {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const getTypologieName = () => {
    if (apartment.rooms === 0) return "Colocation";
    if (apartment.rooms === 1 && apartment.surface_m2 < 23) return "Studio";
    return `T${apartment.rooms}`;
  };

  const handleReserve = () => {
    if (onReserve) {
      onReserve(apartment);
    }
  };

  const getSurfaceDisplay = () => {
    if (apartment.surface_min && apartment.surface_max) {
      return `${apartment.surface_min}-${apartment.surface_max}m²`;
    }
    return `${apartment.surface_m2}m²`;
  };

  return (
    <div className="apartment-card">
      <div className="apartment-card-main-row">
        <div className="apartment-card-header">
          <h3>{getTypologieName()} {getSurfaceDisplay()} - {apartment.city}</h3>
          <span className="apartment-card-postal">{apartment.postal_code}</span>
        </div>

        <div className="apartment-card-dpe">
          <div className={`apartment-card-dpe-label ${apartment.energy_label?.toLowerCase()}`}>
            {apartment.energy_label}
          </div>
          <div className="apartment-card-dpe-text">DPE</div>
        </div>

        <div className="apartment-card-price">
          À partir de {apartment.rent_cc_eur}€
        </div>

        <button
          className={`apartment-card-toggle ${isExpanded ? 'expanded' : ''}`}
          onClick={toggleExpanded}
        >
          Détails
        </button>
      </div>

      <div className={`apartment-card-details ${isExpanded ? 'expanded' : ''}`}>
        <div className="apartment-card-content-row">
          {/* Image à gauche */}
          <div className="apartment-card-image">
            <img
              src="https://booking.ecla.com/_next/image?url=https%3A%2F%2Fuxco-booking-production-public.s3.eu-west-3.amazonaws.com%2Fe35ec262d24370ffc009dcb2d08b0d87.webp&w=1920&q=75"
              alt={`Appartement T${apartment.rooms} à ${apartment.city}`}
              loading="lazy"
            />
          </div>

          {/* Contenu à droite */}
          <div className="apartment-card-right-content">
            {/* Tags */}
            <div className="apartment-card-tags">
              <span className="apartment-card-tag">Surface: {apartment.surface_m2} m²</span>
              <span className="apartment-card-tag">Pièces: {apartment.rooms === 0 ? 'Colocation' : apartment.rooms}</span>
              <span className="apartment-card-tag">Meublé</span>
              {apartment.floor !== undefined && (
                <span className="apartment-card-tag">Étage: {apartment.floor}</span>
              )}
              {apartment.orientation && (
                <span className="apartment-card-tag">Orientation: {apartment.orientation}</span>
              )}
              {apartment.bed_size && (
                <span className="apartment-card-tag">Lit: {apartment.bed_size}cm</span>
              )}
              {apartment.has_ac && (
                <span className="apartment-card-tag">Climatisation</span>
              )}
              <span className="apartment-card-tag">Dispo: {formatDate(apartment.availability_date)}</span>
            </div>

            {/* Description */}
            {apartment.content && (
              <div className="apartment-card-description">
                {apartment.content}
              </div>
            )}

            {/* Bouton Affiner ma réservation */}
            {onReserve && (
              <button className="apartment-card-reserve-btn" onClick={handleReserve}>
                🎯 Affiner ma réservation
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


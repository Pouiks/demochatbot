import { useState } from 'react';

interface ApartmentCardProps {
  apartment: {
    id: string;
    city: string;
    rooms: number;
    surface_m2: number;
    furnished: boolean;
    rent_cc_eur: number;
    availability_date: string;
    energy_label: string;
    postal_code: string;
    content: string;
  };
}

export default function ApartmentCard({ apartment }: ApartmentCardProps) {
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

  return (
    <div className="apartment-card">
      <div className="apartment-card-main-row">
        <div className="apartment-card-header">
          <h3>T{apartment.rooms} - {apartment.city}</h3>
          <span className="apartment-card-postal">{apartment.postal_code}</span>
        </div>

        <div className="apartment-card-dpe">
          <div className={`apartment-card-dpe-label ${apartment.energy_label?.toLowerCase()}`}>
            {apartment.energy_label}
          </div>
          <div className="apartment-card-dpe-text">DPE</div>
        </div>

        <div className="apartment-card-price">
          {apartment.rent_cc_eur}
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
              <span className="apartment-card-tag">Pièces: {apartment.rooms}</span>
              <span className="apartment-card-tag">{apartment.furnished ? "Meublé" : "Non meublé"}</span>
              <span className="apartment-card-tag">Dispo: {formatDate(apartment.availability_date)}</span>
            </div>

            {/* Description */}
            {apartment.content && (
              <div className="apartment-card-description">
                {apartment.content}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


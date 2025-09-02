import React, { useState } from 'react';
import { X } from 'lucide-react';

export default function QuoteModal({ isOpen, onClose }) {
  const [formData, setFormData] = useState({
    n_cin: '',
    valeur_venale: '',
    nature_contrat: '',
    nombre_place: '',
    valeur_a_neuf: '',
    date_premiere_mise_en_circulation: '',
    capital_bris_de_glace: '',
    capital_dommage_collision: '',
    puissance: '',
    classe: ''
  });

  const [loading, setLoading] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validateForm = () => {
    const errors = [];

    if (!formData.n_cin) errors.push("Le numéro CIN est requis.");
    if (!formData.valeur_venale || parseFloat(formData.valeur_venale) <= 0) errors.push("La valeur vénale doit être supérieure à 0.");
    if (!formData.nature_contrat) errors.push("La nature du contrat est requise.");
    if (!formData.nombre_place || parseInt(formData.nombre_place) <= 0) errors.push("Le nombre de places doit être supérieur à 0.");
    if (!formData.date_premiere_mise_en_circulation) errors.push("La date de première mise en circulation est requise.");
    if (!formData.puissance || parseInt(formData.puissance) < 1 || parseInt(formData.puissance) > 6) errors.push("La puissance doit être entre 1 et 6.");
    if (!formData.classe) errors.push("La classe est requise.");

    return errors;
  };

  const handleSubmit = async () => {
    const errors = validateForm();
    if (errors.length > 0) {
      alert(errors.join("\n"));
      return;
    }

    setLoading(true);

    const natureContratMap = {
      "tiers_simple": "r",
      "tiers_complet": "tc",
      "tous_risques": "tr",
      "vol_incendie": "vi"
    };

    const submissionData = {
      n_cin: formData.n_cin,
      valeur_venale: parseFloat(formData.valeur_venale) || 0,
      nature_contrat: natureContratMap[formData.nature_contrat] || "r",
      nombre_place: parseInt(formData.nombre_place) || 1,
      valeur_a_neuf: parseFloat(formData.valeur_a_neuf) || parseFloat(formData.valeur_venale) || 0,
      date_premiere_mise_en_circulation: formData.date_premiere_mise_en_circulation,
      capital_bris_de_glace: parseFloat(formData.capital_bris_de_glace) || 0,
      capital_dommage_collision: parseFloat(formData.capital_dommage_collision) || 0,
      puissance: Math.min(Math.max(parseInt(formData.puissance) || 1, 1), 6),
      classe: parseInt(formData.classe) || 1
    };

    console.log("Submitting data:", submissionData);

    try {
      const token = import.meta.env.VITE_CHAT_API_TOKEN;

      const response = await fetch(`${import.meta.env.VITE_API_URL}/devis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify(submissionData),
      });

      if (!response.ok) throw new Error(`Erreur lors de la génération du devis: ${response.status}`);

      const blob = await response.blob();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'devis.pdf');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);

      setFormData({
        n_cin: '',
        valeur_venale: '',
        nature_contrat: '',
        nombre_place: '',
        valeur_a_neuf: '',
        date_premiere_mise_en_circulation: '',
        capital_bris_de_glace: '',
        capital_dommage_collision: '',
        puissance: '',
        classe: ''
      });
      onClose();

    } catch (error) {
      console.error('Error generating PDF:', error);
      alert('Une erreur est survenue lors de la génération du PDF.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50">
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity duration-300"
        onClick={onClose}
      />

      <div className={`absolute top-0 right-0 h-full w-full max-w-md bg-white shadow-2xl transform transition-transform duration-300 ease-out ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>

        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Demander un devis</h2>
            <p className="text-sm text-gray-500 mt-1">Remplissez le formulaire suivant pour demander un devis</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Form Content */}
        <div className="p-6 overflow-y-auto h-[calc(100vh-200px)]">
          <div className="space-y-6">

            {/* N° CIN */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Numéro CIN</label>
              <input
                type="text"
                value={formData.n_cin}
                onChange={(e) => handleInputChange('n_cin', e.target.value)}
                placeholder="Votre numéro CIN"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>

            {/* Valeur vénale */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Valeur vénale</label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  value={formData.valeur_venale}
                  onChange={(e) => handleInputChange('valeur_venale', e.target.value)}
                  placeholder="0.00"
                  className="w-full px-3 py-2 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
                <span className="absolute right-3 top-2 text-gray-500 text-sm">DT</span>
              </div>
            </div>

            {/* Nature du Contrat */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Nature du contrat</label>
              <select
                value={formData.nature_contrat}
                onChange={(e) => handleInputChange('nature_contrat', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent bg-white appearance-none"
              >
                <option value="">Sélectionner le type de contrat</option>
                <option value="tous_risques">Tous risques</option>
                <option value="tiers_complet">Tiers complet</option>
                <option value="tiers_simple">Tiers simple</option>
                <option value="vol_incendie">Vol et incendie</option>
              </select>
            </div>

            {/* Nombre de places */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Nombre de places</label>
              <input
                type="number"
                min="1"
                value={formData.nombre_place}
                onChange={(e) => handleInputChange('nombre_place', e.target.value)}
                placeholder="5"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>

            {/* Valeur à neuf */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Valeur à neuf</label>
              <div className="relative">
                <input
                  type="number"
                  step="0.01"
                  value={formData.valeur_a_neuf}
                  onChange={(e) => handleInputChange('valeur_a_neuf', e.target.value)}
                  placeholder="0.00"
                  className="w-full px-3 py-2 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
                />
                <span className="absolute right-3 top-2 text-gray-500 text-sm">DT</span>
              </div>
            </div>

            {/* Date première mise en circulation */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date de première mise en circulation</label>
              <input
                type="date"
                value={formData.date_premiere_mise_en_circulation}
                onChange={(e) => handleInputChange('date_premiere_mise_en_circulation', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>

            {/* Capital bris de glace */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Capital bris de glace</label>
              <input
                type="number"
                step="0.01"
                value={formData.capital_bris_de_glace}
                onChange={(e) => handleInputChange('capital_bris_de_glace', e.target.value)}
                placeholder="0.00"
                className="w-full px-3 py-2 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>

            {/* Capital dommage collision */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Capital dommage collision</label>
              <input
                type="number"
                step="0.01"
                value={formData.capital_dommage_collision}
                onChange={(e) => handleInputChange('capital_dommage_collision', e.target.value)}
                placeholder="0.00"
                className="w-full px-3 py-2 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>

            {/* Puissance */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Puissance (CV)</label>
              <input
                type="number"
                min="1"
                max="6"
                value={formData.puissance}
                onChange={(e) => handleInputChange('puissance', e.target.value)}
                placeholder="1"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
            </div>

            {/* Classe */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Classe</label>
              <select
                value={formData.classe}
                onChange={(e) => handleInputChange('classe', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent bg-white appearance-none"
              >
                <option value="">Sélectionner une classe</option>
                <option value="1">Classe 1</option>
                <option value="2">Classe 2</option>
                <option value="3">Classe 3</option>
                <option value="4">Classe 4</option>
                <option value="5">Classe 5</option>
              </select>
            </div>

          </div>
        </div>

        {/* Footer */}
        <div className="absolute bottom-0 left-0 right-0 p-6 bg-white border-t border-gray-100">
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
            >
              Retour au chat
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className={`flex-1 px-4 py-3 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 transition ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              {loading ? 'Génération en cours...' : 'Demander un devis'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}

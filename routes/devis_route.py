import React, { useState } from 'react';
import { X } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';

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
    const requiredFields = [
      'n_cin',
      'valeur_venale',
      'nature_contrat',
      'nombre_place',
      'valeur_a_neuf',
      'date_premiere_mise_en_circulation',
      'capital_bris_de_glace',
      'capital_dommage_collision',
      'puissance',
      'classe'
    ];
    for (let field of requiredFields) {
      if (formData[field] === '' || formData[field] === null) {
        toast.error(`Le champ "${field}" est requis`);
        return false;
      }
    }
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);

    const natureContratMap = {
      "tiers_simple": "r",
      "tiers_complet": "tc",
      "tous_risques": "tr",
      "vol_incendie": "vi"
    };

    const submissionData = {
      n_cin: formData.n_cin,
      valeur_venale: parseFloat(formData.valeur_venale),
      nature_contrat: natureContratMap[formData.nature_contrat] || formData.nature_contrat,
      nombre_place: parseInt(formData.nombre_place),
      valeur_a_neuf: parseFloat(formData.valeur_a_neuf),
      date_premiere_mise_en_circulation: formData.date_premiere_mise_en_circulation,
      capital_bris_de_glace: parseFloat(formData.capital_bris_de_glace),
      capital_dommage_collision: parseFloat(formData.capital_dommage_collision),
      puissance: parseInt(formData.puissance),
      classe: parseInt(formData.classe)
    };

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

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erreur lors de la génération du devis');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'devis.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success('Devis généré avec succès !');
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
      console.error(error);
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <Toaster position="top-right" />
      <div className="fixed inset-0 z-50">
        <div 
          className="absolute inset-0 bg-black bg-opacity-50 transition-opacity duration-300"
          onClick={onClose}
        />

        <div className={`absolute top-0 right-0 h-full w-full max-w-md bg-white shadow-2xl transform transition-transform duration-300 ease-out ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}>
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

          <div className="p-6 overflow-y-auto h-[calc(100vh-200px)]">
            <div className="space-y-6">
              {/* Form fields same as before */}
              {/* Example for n_cin */}
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
              {/* Repeat for other inputs similarly, making sure numeric fields use type="number" */}
            </div>
          </div>

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
    </>
  );
}

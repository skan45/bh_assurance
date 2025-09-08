import React, { useState } from 'react';
import { X } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext';

export default function QuoteModal({ isOpen, onClose }) {
  const { language } = useLanguage(); // 'fr' or 'ar'

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

  const handleSubmit = async () => {
    const submissionData = {
      n_cin: formData.n_cin,
      valeur_venale: parseFloat(formData.valeur_venale) || 0,
      nature_contrat: formData.nature_contrat,
      nombre_place: parseInt(formData.nombre_place) || 0,
      valeur_a_neuf: parseFloat(formData.valeur_a_neuf) || 0,
      date_premiere_mise_en_circulation: formData.date_premiere_mise_en_circulation,
      capital_bris_de_glace: parseFloat(formData.capital_bris_de_glace) || 0,
      capital_dommage_collision: parseFloat(formData.capital_dommage_collision) || 0,
      puissance: parseInt(formData.puissance) || 0,
      classe: parseInt(formData.classe) || 0
    };

    try {
      setLoading(true);
      const apiUrl = import.meta.env.VITE_API_URL; 
      const token = localStorage.getItem('auth_token');

      const response = await fetch(`${apiUrl}/devis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(submissionData)
      });

      if (!response.ok) {
        const text = await response.text();
        console.error('Devis API error:', text);
        alert(language === 'fr'
          ? 'Erreur lors de la récupération du devis. Vérifiez la console.'
          : 'حدث خطأ أثناء استرجاع العرض. تحقق من وحدة التحكم.');
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = language === 'fr' ? 'devis.pdf' : 'عرض.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      onClose();
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
    } catch (error) {
      console.error('Request failed:', error);
      alert(language === 'fr'
        ? 'Erreur réseau lors de la récupération du devis.'
        : 'فشل الشبكة أثناء استرجاع العرض.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity duration-300"
        onClick={onClose}
      />
      
      {/* Modal sliding from right */}
      <div className={`absolute top-0 right-0 h-full w-full max-w-md bg-white shadow-2xl transform transition-transform duration-300 ease-out ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              {language === 'fr' ? 'Demander un devis' : 'طلب عرض'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {language === 'fr' 
                ? 'Remplissez le formulaire suivant pour demander un devis' 
                : 'املأ النموذج التالي لطلب عرض'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto h-[calc(100vh-200px)] space-y-6">
          {/* N° CIN */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Numéro CIN' : 'رقم البطاقة الوطنية'}
            </label>
            <input
              type="text"
              value={formData.n_cin}
              onChange={(e) => handleInputChange('n_cin', e.target.value)}
              placeholder={language === 'fr' ? 'Votre numéro CIN' : 'أدخل رقم البطاقة'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            />
          </div>

          {/* Valeur Vénale */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Valeur vénale' : 'القيمة السوقية'}
            </label>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Nature du contrat' : 'نوع العقد'}
            </label>
            <select
              value={formData.nature_contrat}
              onChange={(e) => handleInputChange('nature_contrat', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent bg-white appearance-none"
            >
              <option value="">
                {language === 'fr' ? 'Sélectionner le type de contrat' : 'اختر نوع العقد'}
              </option>
              <option value="r">{language === 'fr' ? 'Tous risques' : 'جميع المخاطر'}</option>
              <option value="tc">{language === 'fr' ? 'Tiers complet' : 'الطرف الثالث كامل'}</option>
              <option value="ts">{language === 'fr' ? 'Tiers simple' : 'الطرف الثالث بسيط'}</option>
              <option value="vi">{language === 'fr' ? 'Vol et incendie' : 'سرقة وحريق'}</option>
            </select>
          </div>

          {/* Nombre de Places */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Nombre de places' : 'عدد المقاعد'}
            </label>
            <input
              type="number"
              min="1"
              value={formData.nombre_place}
              onChange={(e) => handleInputChange('nombre_place', e.target.value)}
              placeholder={language === 'fr' ? '5' : '٥'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            />
          </div>

          {/* Valeur à Neuf */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Valeur à neuf' : 'القيمة الجديدة'}
            </label>
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

          {/* Date Première Mise en Circulation */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Date de première mise en circulation' : 'تاريخ أول تشغيل'}
            </label>
            <input
              type="date"
              value={formData.date_premiere_mise_en_circulation}
              onChange={(e) => handleInputChange('date_premiere_mise_en_circulation', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            />
          </div>

          {/* Capital Bris de Glace */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Capital bris de glace' : 'رأس المال كسر الزجاج'}
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.01"
                value={formData.capital_bris_de_glace}
                onChange={(e) => handleInputChange('capital_bris_de_glace', e.target.value)}
                placeholder="0.00"
                className="w-full px-3 py-2 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
              <span className="absolute right-3 top-2 text-gray-500 text-sm">DT</span>
            </div>
          </div>

          {/* Capital Dommage Collision */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Capital dommage collision' : 'رأس المال الضرر التصادمي'}
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.01"
                value={formData.capital_dommage_collision}
                onChange={(e) => handleInputChange('capital_dommage_collision', e.target.value)}
                placeholder="0.00"
                className="w-full px-3 py-2 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
              />
              <span className="absolute right-3 top-2 text-gray-500 text-sm">DT</span>
            </div>
          </div>

          {/* Puissance */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Puissance (CV)' : 'القوة (حصان)'}
            </label>
            <input
              type="number"
              min="1"
              value={formData.puissance}
              onChange={(e) => handleInputChange('puissance', e.target.value)}
              placeholder={language === 'fr' ? '100' : '١٠٠'}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            />
          </div>

          {/* Classe */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {language === 'fr' ? 'Classe' : 'الفئة'}
            </label>
            <select
              value={formData.classe}
              onChange={(e) => handleInputChange('classe', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent bg-white appearance-none"
            >
              <option value="">
                {language === 'fr' ? 'Sélectionner une classe' : 'اختر الفئة'}
              </option>
              {[1, 2, 3, 4, 5].map(c => (
                <option key={c} value={c}>
                  {language === 'fr' ? `Classe ${c}` : `الفئة ${c}`}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="absolute bottom-0 left-0 right-0 p-6 bg-white border-t border-gray-100">
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
            >
              {language === 'fr' ? 'Retour au chat' : 'العودة إلى المحادثة'}
            </button>
            <button
              onClick={handleSubmit}
              disabled={loading}
              className={`flex-1 px-4 py-3 rounded-xl text-sm font-medium transition ${
                loading
                  ? 'bg-gray-400 text-white cursor-not-allowed'
                  : 'bg-red-600 text-white hover:bg-red-700'
              }`}
            >
              {loading
                ? language === 'fr' ? '⏳ Chargement...' : '⏳ جاري التحميل...'
                : language === 'fr' ? 'Demander un devis' : 'طلب عرض'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

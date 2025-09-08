import React, { useState } from 'react';
import { X } from 'lucide-react';
import { useLanguage } from '@/context/LanguageContext'; // Assume you have a LanguageContext

export default function ContactModal({ isOpen, onClose }) {
  const { language } = useLanguage(); // 'fr' or 'ar'

  const [formData, setFormData] = useState({
    sujet: '',
    message: ''
  });
  const [loading, setLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    // Basic validation
    if (!formData.message) {
      alert(language === 'fr' 
        ? 'Veuillez saisir votre message.' 
        : 'يرجى إدخال رسالتك.');
      return;
    }

    try {
      setLoading(true);
      const apiUrl = import.meta.env.VITE_API_URL; 
      const token = localStorage.getItem('auth_token');

      const response = await fetch(`${apiUrl}/contact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const text = await response.text();
        console.error('Contact API error:', text);
        alert(language === 'fr'
          ? 'Erreur lors de l\'envoi du message. Veuillez réessayer.'
          : 'حدث خطأ أثناء إرسال الرسالة. حاول مرة أخرى.');
        return;
      }

      // Show success popup
      setShowSuccess(true);

      // Reset form
      setFormData({ sujet: '', message: '' });

      // Close modal and hide success popup after 3 seconds
      setTimeout(() => {
        setShowSuccess(false);
        onClose();
      }, 3000);
    } catch (error) {
      console.error('Request failed:', error);
      alert(language === 'fr'
        ? 'Erreur réseau lors de l\'envoi du message.'
        : 'فشل الشبكة أثناء إرسال الرسالة.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
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
                {language === 'fr' ? 'Contacter un conseiller' : 'التواصل مع مستشار'}
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {language === 'fr' 
                  ? 'Envoyez-nous votre message et nous vous recontacterons' 
                  : 'أرسل رسالتك وسيتواصل معك مستشار'}
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
          <div className="p-6 overflow-y-auto h-[calc(100vh-200px)] space-y-4">

            {/* Sujet */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {language === 'fr' ? 'Sujet' : 'الموضوع'}
              </label>
              <select
                value={formData.sujet}
                onChange={(e) => handleInputChange('sujet', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent bg-white"
              >
                <option value="">
                  {language === 'fr' ? 'Sélectionner un sujet' : 'اختر الموضوع'}
                </option>
                <option value="demande_info">{language === 'fr' ? 'Demande d\'information' : 'طلب معلومات'}</option>
                <option value="modification_contrat">{language === 'fr' ? 'Modification de contrat' : 'تعديل العقد'}</option>
                <option value="sinistre">{language === 'fr' ? 'Déclaration de sinistre' : 'الإبلاغ عن حادث'}</option>
                <option value="reclamation">{language === 'fr' ? 'Réclamation' : 'شكوى'}</option>
                <option value="autre">{language === 'fr' ? 'Autre' : 'أخرى'}</option>
              </select>
            </div>

            {/* Message */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {language === 'fr' ? 'Message *' : 'الرسالة *'}
              </label>
              <textarea
                value={formData.message}
                onChange={(e) => handleInputChange('message', e.target.value)}
                placeholder={language === 'fr' ? 'Décrivez votre demande en détail...' : 'صف طلبك بالتفصيل...'}
                rows={8}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none"
                required
              />
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
                {loading ? (language === 'fr' ? '⏳ Envoi...' : '⏳ جاري الإرسال...') : (language === 'fr' ? 'Envoyer' : 'إرسال')}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Success Popup */}
      {showSuccess && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center">
          <div className="absolute inset-0 bg-black bg-opacity-30" />
          <div className="relative bg-white rounded-2xl p-6 mx-4 max-w-sm w-full shadow-2xl transform animate-in fade-in duration-300 zoom-in-95">
            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {language === 'fr' ? 'Message envoyé !' : 'تم إرسال الرسالة!'}
              </h3>
              <p className="text-sm text-gray-600">
                {language === 'fr'
                  ? 'Votre message a été envoyé avec succès. Un conseiller vous contactera bientôt.'
                  : 'تم إرسال رسالتك بنجاح. سيتواصل معك مستشار قريبًا.'}
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

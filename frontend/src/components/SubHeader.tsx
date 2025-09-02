import { useState } from 'react';
import QuoteModal from './QuoteModal'; // Import the modal component
import ContactModal from './ContactModal'; // Import the contact modal component

export default function SubHeader() {
  const [isQuoteModalOpen, setIsQuoteModalOpen] = useState(false);
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);

  return (
    <>
      <div className="flex items-center justify-between bg-white px-6 py-3">
        {/* Left Text */}
        <div className="text-gray-600 font-medium">
          Parlez avec <span className="font-semibold text-gray-800">BH Hub</span> by BH Assurances
        </div>
         
        {/* Right Buttons */}
        <div className="flex gap-3">
          <button 
            onClick={() => setIsQuoteModalOpen(true)}
            className="px-4 py-2 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
          >
            Demander un devis
          </button>
          <button 
            onClick={() => setIsContactModalOpen(true)}
            className="px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 transition"
          >
            Contacter un conseiller
          </button>
        </div>
      </div>

      {/* Quote Modal */}
      <QuoteModal 
        isOpen={isQuoteModalOpen} 
        onClose={() => setIsQuoteModalOpen(false)} 
      />

      {/* Contact Modal */}
      <ContactModal 
        isOpen={isContactModalOpen} 
        onClose={() => setIsContactModalOpen(false)} 
      />
    </>
  );
}
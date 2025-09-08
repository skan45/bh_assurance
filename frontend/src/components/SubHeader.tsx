import { useState } from "react";
import QuoteModal from "./QuoteModal";
import ContactModal from "./ContactModal";
import { useLanguage } from "@/context/LanguageContext";

export default function SubHeader() {
  const [isQuoteModalOpen, setIsQuoteModalOpen] = useState(false);
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);
  const { language } = useLanguage();

  // Text based on language
  const requestQuoteText = language === "fr" ? "Demander un devis" : "طلب عرض";
  const contactAdvisorText = language === "fr" ? "Contacter un conseiller" : "الاتصال بمستشار";
  const talkWithText = language === "fr" ? "Parlez avec" : "تحدث مع";
  const bhHubText = "BH Hub"; // Name stays same

  return (
    <>
      <div className="flex items-center justify-between bg-white px-6 py-3">
        {/* Left Text */}
        <div className="text-gray-600 font-medium flex items-center gap-1">
          {language === "fr" ? (
            <>
              {talkWithText} <span className="font-semibold text-gray-800">{bhHubText}</span> by BH Assurances
            </>
          ) : (
            <>
              <span className="font-semibold text-gray-800">{bhHubText} by BH Assurances</span> {talkWithText}
            </>
          )}
        </div>

        {/* Right Buttons */}
        <div className="flex gap-3">
          <button 
            onClick={() => setIsQuoteModalOpen(true)}
            className="px-4 py-2 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
          >
            {requestQuoteText}
          </button>
          <button 
            onClick={() => setIsContactModalOpen(true)}
            className="px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 transition"
          >
            {contactAdvisorText}
          </button>
        </div>
      </div>

      {/* Modals */}
      <QuoteModal 
        isOpen={isQuoteModalOpen} 
        onClose={() => setIsQuoteModalOpen(false)} 
      />
      <ContactModal 
        isOpen={isContactModalOpen} 
        onClose={() => setIsContactModalOpen(false)} 
      />
    </>
  );
}

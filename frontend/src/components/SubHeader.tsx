export default function SubHeader() {
  return (
    <div className="flex items-center justify-between bg-white px-6 py-3">
      {/* Left Text */}
      <div className="text-gray-600 font-medium">
        Parlez avec <span className="font-semibold text-gray-800">BH Hub</span> by BH Assurances
      </div>
       
      {/* Right Buttons */}
      <div className="flex gap-3">
        <button className="px-4 py-2 border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-100 transition">
          Demander un devis
        </button>
        <button className="px-4 py-2 bg-red-600 text-white rounded-xl text-sm font-medium hover:bg-red-700 transition">
          Contacter un conseiller
        </button>
      </div>
    </div>
  );
}
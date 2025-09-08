import { Mail } from "lucide-react";
import { useLanguage } from "@/context/LanguageContext";

const Header = () => {
  const { language, setLanguage } = useLanguage();

  return (
    <header className="h-16 bg-background border border-border rounded-full mx-4 my-2 px-6 flex items-center justify-between shadow-sm">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <img
          src="/BH-Assurance.png"
          alt="BH Assurance"
          className="h-15 w-15 object-contain"
        />
      </div>

      {/* Email / User Info and Language Switcher */}
      <div className="flex items-center gap-4">
        {/* Email */}
        <div className="flex items-center gap-2 text-sm text-foreground">
          <Mail className="w-4 h-4 text-muted-foreground" />
          <span className="text-muted-foreground">contact@bhassurance.com</span>
        </div>

        {/* Language Flags */}
        <div className="flex items-center gap-2">
          {/* French Flag */}
          <img
            src="https://upload.wikimedia.org/wikipedia/en/c/c3/Flag_of_France.svg"
            alt="Français"
            className={`w-6 h-4 cursor-pointer border ${language === "fr" ? "border-red-600 rounded" : "border-transparent"}`}
            onClick={() => setLanguage("fr")}
          />
          {/* Tunisian Flag */}
          <img
            src="https://upload.wikimedia.org/wikipedia/commons/c/ce/Flag_of_Tunisia.svg"
            alt="العربية"
            className={`w-6 h-4 cursor-pointer border ${language === "ar" ? "border-red-600 rounded" : "border-transparent"}`}
            onClick={() => setLanguage("ar")}
          />
        </div>
      </div>
    </header>
  );
};

export default Header;

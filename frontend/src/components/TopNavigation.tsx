import { useUser } from "@/context/UserContext";
import { useLanguage } from "@/context/LanguageContext";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const anonymousAvatar = "https://www.gravatar.com/avatar/?d=mp&f=y"; // default anonymous avatar

// Online flag URLs
const FR_FLAG = "https://upload.wikimedia.org/wikipedia/en/c/c3/Flag_of_France.svg";
const TN_FLAG = "https://upload.wikimedia.org/wikipedia/commons/c/ce/Flag_of_Tunisia.svg";

interface TopNavigationProps {
  onLogout: () => void;
}

const TopNavigation = ({ onLogout }: TopNavigationProps) => {
  const { user } = useUser();
  const navigate = useNavigate();
  const { language, setLanguage } = useLanguage();

  const isVisitor = user?.visitor === true;
  const displayName = user?.full_name || (isVisitor ? "Visiteur" : "Loading...");
  const displayEmail = user?.email || (isVisitor ? "" : "Loading...");

  return (
    <header className="h-16 bg-background border border-border rounded-3xl mx-4 my-2 px-6 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <img src="/BH-Assurance.png" alt="BH Assurance" className="h-15 w-15 rounded-xl" />
      </div>

      <div className="flex items-center gap-4">
        {/* Language buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => setLanguage("fr")}
            title="Français"
            className={`p-1 rounded-full border ${language === "fr" ? "border-primary" : "border-gray-300"}`}
          >
            <img src={FR_FLAG} alt="French" className="h-6 w-6 rounded-full" />
          </button>
          <button
            onClick={() => setLanguage("ar")}
            title="Arabic"
            className={`p-1 rounded-full border ${language === "ar" ? "border-primary" : "border-gray-300"}`}
          >
            <img src={TN_FLAG} alt="Arabic" className="h-6 w-6 rounded-full" />
          </button>
        </div>

        {/* User avatar / login */}
        {isVisitor ? (
          <Button
            onClick={() => navigate("/login")}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition"
          >
            {language === "fr" ? "Connexion" : "تسجيل الدخول"}
          </Button>
        ) : (
          <>
            <Avatar className="h-10 w-10 rounded-full">
              <AvatarImage src={anonymousAvatar} alt={displayName} />
              <AvatarFallback className="bg-primary text-primary-foreground font-medium">
                {displayName
                  .split(" ")
                  .map((n) => n[0])
                  .join("") || "SG"}
              </AvatarFallback>
            </Avatar>
            <div className="text-sm">
              <div className="font-medium text-foreground">{displayName}</div>
              <div className="text-muted-foreground">{displayEmail}</div>
            </div>
            <Button
              onClick={onLogout}
              className="px-3 py-1 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition"
            >
              {language === "fr" ? "Déconnexion" : "تسجيل الخروج"}
            </Button>
          </>
        )}
      </div>
    </header>
  );
};

export default TopNavigation;

import { Mail } from "lucide-react";

const Header = () => {
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

      {/* Email / User Info */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-foreground">
          <Mail className="w-4 h-4 text-muted-foreground" />
          <span className="text-muted-foreground">contact@bhassurance.com</span>
        </div>
      </div>
    </header>
  );
};

export default Header;

import { useUser } from "@/context/UserContext";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const anonymousAvatar = "https://www.gravatar.com/avatar/?d=mp&f=y"; // default anonymous avatar

const TopNavigation = () => {
  const { user } = useUser();
  const navigate = useNavigate();

  // Determine if the user is a visitor
  const isVisitor = user?.visitor === true;

  // Determine display name and email
  const displayName = user?.full_name || (isVisitor ? "Visiteur" : "Loading...");
  const displayEmail = user?.email || (isVisitor ? "" : "Loading...");

  return (
    <header className="h-16 bg-background border border-border rounded-3xl mx-4 my-2 px-6 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <img src="/BH-Assurance.png" alt="BH Assurance" className="h-15 w-15 rounded-xl" />
      </div>
      <div className="flex items-center gap-4">
        {isVisitor ? (
          <Button
            onClick={() => navigate("/login")}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 transition"
          >
            Login
          </Button>
        ) : (
          <>
            <Avatar className="h-10 w-10 rounded-full">
              <AvatarImage src={anonymousAvatar} alt={displayName} />
              <AvatarFallback className="bg-primary text-primary-foreground font-medium">
                {displayName.split(" ").map(n => n[0]).join("") || "SG"}
              </AvatarFallback>
            </Avatar>
            <div className="text-sm">
              <div className="font-medium text-foreground">{displayName}</div>
              <div className="text-muted-foreground">{displayEmail}</div>
            </div>
          </>
        )}
      </div>
    </header>
  );
};

export default TopNavigation;

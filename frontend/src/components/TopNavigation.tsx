import { useUser } from "@/context/UserContext";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import avatarImage from "@/assets/avatar.png";

const TopNavigation = () => {
  const { user } = useUser();

  return (
    <header className="h-16 bg-background border border-border rounded-full mx-4 my-2 px-6 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <img src="/BH-Assurance.png" alt="BH Assurance" className="h-15 w-15" />
      </div>
      <div className="flex items-center gap-4">
        <Avatar className="h-10 w-10">
          <AvatarImage src={user?.avatarUrl || avatarImage} alt={user?.username || "User"} />
          <AvatarFallback className="bg-primary text-primary-foreground font-medium">
            {user?.username ? user.username.split(" ").map(n => n[0]).join("") : "SG"}
          </AvatarFallback>
        </Avatar>
        <div className="text-sm">
          <div className="font-medium text-foreground">{user?.username || "Loading..."}</div>
          <div className="text-muted-foreground">{user?.email || "Loading..."}</div>
        </div>
      </div>
    </header>
  );
};

export default TopNavigation;

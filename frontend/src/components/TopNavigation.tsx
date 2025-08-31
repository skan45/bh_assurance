import { Button } from "@/components/ui/button"; 
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"; 
import { Shield } from "lucide-react"; 
import avatarImage from "@/assets/avatar.png"; 
 
 
const TopNavigation = () => { 
  return ( 
    <header className="h-16 bg-background border border-border rounded-full mx-4 my-2 px-6 flex items-center justify-between shadow-sm"> 
      {/* Logo */} 
      <div className="flex items-center gap-3"> 
        <img src="./BH-Assurance.png" alt="BH Assurance" className="h-15 w-15" />
      </div> 
 
      {/* Right side - Profile */} 
      <div className="flex items-center gap-4"> 
        {/* User Profile */} 
        <div className="flex items-center gap-3"> 
          <Avatar className="h-10 w-10"> 
            <AvatarImage src={avatarImage} alt="Mohamed Zgolli" /> 
            <AvatarFallback className="bg-primary text-primary-foreground font-medium">MZ</AvatarFallback> 
          </Avatar> 
          <div className="text-sm"> 
            <div className="font-medium text-foreground">Mohamed Zgolli</div> 
            <div className="text-muted-foreground">mohamedzgolli@gmail.com</div> 
          </div> 
        </div> 
      </div> 
    </header> 
  ); 
}; 
 
export default TopNavigation;
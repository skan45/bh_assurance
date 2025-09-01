import { createContext, useContext, useState, useEffect, ReactNode } from "react";

interface User {
  username: string;
  email: string;
  avatarUrl?: string;
}

interface UserContextType {
  user: User | null;
  setUser: (user: User) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const token = import.meta.env.VITE_CHAT_API_TOKEN;

  useEffect(() => {
    if (!user) {
      fetch(`${import.meta.env.VITE_API_URL}/user/profile`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(res => res.json())
        .then(data => setUser(data))
        .catch(console.error);
    }
  }, []);

  return <UserContext.Provider value={{ user, setUser }}>{children}</UserContext.Provider>;
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) throw new Error("useUser must be used within UserProvider");
  return context;
};

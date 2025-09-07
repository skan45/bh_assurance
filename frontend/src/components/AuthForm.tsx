import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff, Mail, Lock, User } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface AuthFormProps {
  onAuthSuccess: () => void;
}

const AuthForm = ({ onAuthSuccess }: AuthFormProps) => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  // -------------------- LOGIN --------------------
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.currentTarget as HTMLFormElement);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem("auth_token", data.access_token);
        toast({ title: "Connexion réussie", description: "Bienvenue dans votre espace BH Assurance" });
        onAuthSuccess();
      } else {
        toast({
          title: "Erreur de connexion",
          description: data.detail || "Identifiants incorrects",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Login error:", error);
      toast({
        title: "Erreur de connexion",
        description: "Une erreur s'est produite. Veuillez réessayer.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // -------------------- REGISTER --------------------
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    const formData = new FormData(e.currentTarget as HTMLFormElement);
    const full_name = formData.get("fullName") as string;
    const email = formData.get("registerEmail") as string;
    const password = formData.get("registerPassword") as string;
    const confirmPassword = formData.get("confirmPassword") as string;
    const cin = (formData.get("cin") as string)?.trim();
    const matriculeFiscale = (formData.get("matriculeFiscale") as string)?.trim();

    if (!cin && !matriculeFiscale) {
      toast({
        title: "Erreur",
        description: "Veuillez renseigner le CIN ou le matricule fiscale",
        variant: "destructive",
      });
      setIsLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      toast({ title: "Erreur", description: "Les mots de passe ne correspondent pas", variant: "destructive" });
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name,
          email,
          password,
          cin: cin || null,
          matricule_fiscale: matriculeFiscale || null,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: "Inscription réussie",
          description: "Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.",
        });
        const loginTab = document.querySelector('[value="login"]') as HTMLElement;
        loginTab?.click();
      } else {
        toast({
          title: "Erreur d'inscription",
          description: data.detail || "Une erreur s'est produite lors de l'inscription",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Register error:", error);
      toast({
        title: "Erreur d'inscription",
        description: "Une erreur s'est produite. Veuillez réessayer.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // -------------------- JSX --------------------
  return (
    <Card className="w-full max-w-md shadow-card">
      <CardHeader className="text-center pb-2">
        <h2 className="text-2xl font-bold text-secondary">Espace Client</h2>
        <p className="text-muted-foreground">Accédez à votre compte</p>
      </CardHeader>
      <CardContent className="p-6">
        <Tabs defaultValue="login" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="login" className="text-sm font-medium">Connexion</TabsTrigger>
            <TabsTrigger value="register" className="text-sm font-medium">Inscription</TabsTrigger>
          </TabsList>

          {/* -------------------- LOGIN Tab -------------------- */}
          <TabsContent value="login" className="space-y-4">
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium text-secondary">Adresse email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="votre@email.com"
                    className="pl-10 h-12 focus:ring-primary focus:border-primary"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-medium text-secondary">Mot de passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    className="pl-10 pr-10 h-12 focus:ring-primary focus:border-primary"
                    required
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-colors"
                    disabled={isLoading}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox id="remember" />
                <Label htmlFor="remember" className="text-sm text-muted-foreground">Se souvenir de moi</Label>
              </div>

              <Button type="submit" className="w-full h-12 bg-primary hover:bg-primary/90 text-primary-foreground font-medium" disabled={isLoading}>
                {isLoading ? <> <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div> Connexion... </> : "Se connecter"}
              </Button>
            </form>
          </TabsContent>

          {/* -------------------- REGISTER Tab -------------------- */}
          <TabsContent value="register" className="space-y-4">
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="fullName" className="text-sm font-medium text-secondary">Nom complet</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="fullName"
                    name="fullName"
                    type="text"
                    placeholder="Jean Dupont"
                    className="pl-10 h-12 focus:ring-primary focus:border-primary"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="registerEmail" className="text-sm font-medium text-secondary">Adresse email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="registerEmail"
                    name="registerEmail"
                    type="email"
                    placeholder="votre@email.com"
                    className="pl-10 h-12 focus:ring-primary focus:border-primary"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="registerPassword" className="text-sm font-medium text-secondary">Mot de passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="registerPassword"
                    name="registerPassword"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    className="pl-10 pr-10 h-12 focus:ring-primary focus:border-primary"
                    required
                    disabled={isLoading}
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-colors" disabled={isLoading}>
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword" className="text-sm font-medium text-secondary">Confirmer le mot de passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="••••••••"
                    className="pl-10 pr-10 h-12 focus:ring-primary focus:border-primary"
                    required
                    disabled={isLoading}
                  />
                  <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-3 top-3 text-muted-foreground hover:text-foreground transition-colors" disabled={isLoading}>
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="cin" className="text-sm font-medium text-secondary">CIN</Label>
                <Input id="cin" name="cin" type="text" placeholder="12345678" className="h-12 focus:ring-primary focus:border-primary" disabled={isLoading} />
              </div>

              <div className="space-y-2">
                <Label htmlFor="matriculeFiscale" className="text-sm font-medium text-secondary">Matricule Fiscale</Label>
                <Input id="matriculeFiscale" name="matriculeFiscale" type="text" placeholder="987654321" className="h-12 focus:ring-primary focus:border-primary" disabled={isLoading} />
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox id="terms" required />
                <Label htmlFor="terms" className="text-sm text-muted-foreground">
                  J'accepte les{" "}
                  <button type="button" className="text-primary hover:text-primary/80 transition-colors underline">conditions d'utilisation</button>
                </Label>
              </div>

              <Button type="submit" className="w-full h-12 bg-primary hover:bg-primary/90 text-primary-foreground font-medium" disabled={isLoading}>
                {isLoading ? <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>Inscription...
                </> : "S'inscrire"}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default AuthForm;


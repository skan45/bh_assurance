import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Eye, EyeOff, Mail, Lock, User } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useLanguage } from "@/context/LanguageContext";
import { useUser } from "@/context/UserContext";

interface AuthFormProps {
  onAuthSuccess: () => void;
}

const translations = {
  fr: {
    login: {
      title: "Espace Client",
      subtitle: "Accédez à votre compte",
      email: "Adresse email",
      password: "Mot de passe",
      remember: "Se souvenir de moi",
      loginButton: "Se connecter",
      loginError: "Identifiants incorrects",
      loginNetworkError: "Une erreur s'est produite. Veuillez réessayer.",
    },
    register: {
      fullName: "Nom complet",
      email: "Adresse email",
      password: "Mot de passe",
      confirmPassword: "Confirmer le mot de passe",
      cin: "CIN",
      matriculeFiscale: "Matricule Fiscale",
      terms: "J'accepte les conditions d'utilisation",
      registerButton: "S'inscrire",
      passwordMismatch: "Les mots de passe ne correspondent pas",
      missingID: "Veuillez renseigner le CIN ou le matricule fiscale",
    },
  },
  ar: {
    login: {
      title: "مساحة العميل",
      subtitle: "قم بالوصول إلى حسابك",
      email: "البريد الإلكتروني",
      password: "كلمة المرور",
      remember: "تذكرني",
      loginButton: "تسجيل الدخول",
      loginError: "بيانات الدخول غير صحيحة",
      loginNetworkError: "حدث خطأ، حاول مرة أخرى",
    },
    register: {
      fullName: "الاسم الكامل",
      email: "البريد الإلكتروني",
      password: "كلمة المرور",
      confirmPassword: "تأكيد كلمة المرور",
      cin: "CIN",
      matriculeFiscale: "الرقم الضريبي",
      terms: "أوافق على شروط الاستخدام",
      registerButton: "تسجيل",
      passwordMismatch: "كلمات المرور غير متطابقة",
      missingID: "يرجى إدخال CIN أو الرقم الضريبي",
    },
  },
};

const AuthForm = ({ onAuthSuccess }: AuthFormProps) => {
  const { language } = useLanguage();
  const t = translations[language];
  const { fetchUserProfile } = useUser();

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
        toast({ title: t.login.loginButton, description: t.login.title });

        // Fetch user profile immediately after login
        await fetchUserProfile();

        onAuthSuccess();
      } else {
        toast({ title: t.login.loginError, description: data.detail, variant: "destructive" });
      }
    } catch (error) {
      toast({ title: t.login.loginError, description: t.login.loginNetworkError, variant: "destructive" });
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
      toast({ title: t.register.missingID, variant: "destructive" });
      setIsLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      toast({ title: t.register.passwordMismatch, variant: "destructive" });
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name, email, password, cin: cin || null, matricule_fiscale: matriculeFiscale || null }),
      });

      const data = await response.json();

      if (response.ok) {
        toast({ title: t.register.registerButton, description: t.registerButton });
        const loginTab = document.querySelector('[value="login"]') as HTMLElement;
        loginTab?.click();
      } else {
        toast({ title: t.register.registerButton, description: data.detail, variant: "destructive" });
      }
    } catch (error) {
      toast({ title: t.register.registerButton, description: t.login.loginNetworkError, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md shadow-card">
      <CardHeader className="text-center pb-2">
        <h2 className="text-2xl font-bold text-secondary">{t.login.title}</h2>
        <p className="text-muted-foreground">{t.login.subtitle}</p>
      </CardHeader>
      <CardContent className="p-6">
        <Tabs defaultValue="login" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="login">{language === "fr" ? "Connexion" : "تسجيل الدخول"}</TabsTrigger>
            <TabsTrigger value="register">{language === "fr" ? "Inscription" : "تسجيل"}</TabsTrigger>
          </TabsList>

          {/* LOGIN FORM */}
          <TabsContent value="login" className="space-y-4">
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">{t.login.email}</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input id="email" name="email" placeholder={t.login.email} className="pl-10 h-12" required />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">{t.login.password}</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    className="pl-10 pr-10 h-12"
                    required
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-3">
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox id="remember" />
                <Label htmlFor="remember">{t.login.remember}</Label>
              </div>

              <Button type="submit" className="w-full h-12 bg-primary hover:bg-primary/90 text-primary-foreground font-medium">
                {isLoading ? "Connexion..." : t.login.loginButton}
              </Button>
            </form>
          </TabsContent>

          {/* REGISTER FORM */}
          <TabsContent value="register" className="space-y-4">
            <form onSubmit={handleRegister} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="fullName">{t.register.fullName}</Label>
                <Input id="fullName" name="fullName" placeholder={t.register.fullName} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="registerEmail">{t.register.email}</Label>
                <Input id="registerEmail" name="registerEmail" placeholder={t.register.email} required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="registerPassword">{t.register.password}</Label>
                <Input id="registerPassword" name="registerPassword" type={showPassword ? "text" : "password"} placeholder="••••••••" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">{t.register.confirmPassword}</Label>
                <Input id="confirmPassword" name="confirmPassword" type={showConfirmPassword ? "text" : "password"} placeholder="••••••••" required />
              </div>
              <div className="space-y-2">
                <Label htmlFor="cin">{t.register.cin}</Label>
                <Input id="cin" name="cin" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="matriculeFiscale">{t.register.matriculeFiscale}</Label>
                <Input id="matriculeFiscale" name="matriculeFiscale" />
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox id="terms" required />
                <Label htmlFor="terms">{t.register.terms}</Label>
              </div>
              <Button type="submit" className="w-full h-12 bg-primary hover:bg-primary/90 text-primary-foreground font-medium">
                {isLoading ? "Inscription..." : t.register.registerButton}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default AuthForm;

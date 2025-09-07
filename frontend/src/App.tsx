import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";

import NotFound from "./pages/NotFound";
import TopNavigation from "./components/TopNavigation";
import SubHeader from "./components/SubHeader";
import Sidebar from "./components/Sidebar";
import ChatInterface from "./components/ChatInterface";
import AuthForm from "./components/AuthForm";
import Header from "./components/AuthHeader"; // Your auth header

const queryClient = new QueryClient();

/* -------------------------------
   Layouts
-------------------------------- */

// Main layout for authenticated/un-authenticated app routes
const MainLayout = ({ children, onLogout }: { children: React.ReactNode; onLogout: () => void }) => (
  <div className="h-screen flex flex-col bg-background">
    {/* Top bar */}
    <TopNavigation onLogout={onLogout} />

    {/* SubHeader */}
    <SubHeader />

    {/* Main layout with sidebar */}
    <div className="flex-1 flex overflow-hidden">
      <Sidebar />
      {children}
    </div>
  </div>
);

// Auth layout for login/register
const AuthLayout = ({ children }: { children: React.ReactNode }) => (
  <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
    <Header />
    <div className="flex items-center justify-center min-h-[calc(100vh-80px)] p-4">
      {children}
    </div>
  </div>
);

// Wrapper for login route that redirects on success
const LoginWrapper = ({ setIsAuthenticated }: { setIsAuthenticated: (val: boolean) => void }) => {
  const navigate = useNavigate();

  return (
    <AuthLayout>
      <AuthForm
        onAuthSuccess={() => {
          setIsAuthenticated(true);
          navigate("/"); // redirect to home after login
        }}
      />
    </AuthLayout>
  );
};

/* -------------------------------
   App
-------------------------------- */

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication status on app load
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("auth_token");
      setIsAuthenticated(!!token);
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            {/* Main app routes */}
            <Route
              path="/"
              element={
                <MainLayout onLogout={() => setIsAuthenticated(false)}>
                  <ChatInterface />
                </MainLayout>
              }
            />
            <Route
              path="/chat/:chatId"
              element={
                <MainLayout onLogout={() => setIsAuthenticated(false)}>
                  <ChatInterface />
                </MainLayout>
              }
            />

            {/* Auth route (standalone layout, no nav/sidebar) */}
            <Route
              path="/login"
              element={<LoginWrapper setIsAuthenticated={setIsAuthenticated} />}
            />

            {/* 404 page */}
            <Route
              path="*"
              element={
                <MainLayout onLogout={() => setIsAuthenticated(false)}>
                  <NotFound />
                </MainLayout>
              }
            />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;

import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useState, useEffect } from "react";

import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import TopNavigation from "./components/TopNavigation";
import SubHeader from "./components/SubHeader";
import Sidebar from "./components/Sidebar";
import ChatInterface from "./components/ChatInterface";
import AuthForm from "./components/AuthForm";
import Header from "./components/AuthHeader"; // Your auth header

const queryClient = new QueryClient();

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication status on app load
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('auth_token');
      // You can add more validation here like token expiry check
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

  // Show authentication form if not authenticated
  if (!isAuthenticated) {
    return (
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
            <Header />
            <div className="flex items-center justify-center min-h-[calc(100vh-80px)] p-4">
              <AuthForm onAuthSuccess={() => setIsAuthenticated(true)} />
            </div>
          </div>
        </TooltipProvider>
      </QueryClientProvider>
    );
  }

  // Show main app if authenticated
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <div className="h-screen flex flex-col bg-background">
            {/* Top bar */}
            <TopNavigation onLogout={() => setIsAuthenticated(false)} />
            
            {/* SubHeader right below TopNavigation */}
            <SubHeader />
            
            {/* Main layout */}
            <div className="flex-1 flex overflow-hidden">
              <Sidebar />
              <Routes>
                {/* Default chat interface */}
                <Route path="/" element={<ChatInterface />} />
                
                {/* Specific chat room */}
                <Route path="/chat/:chatId" element={<ChatInterface />} />
                
                {/* 404 page */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </div>
          </div>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  );
};

export default App;
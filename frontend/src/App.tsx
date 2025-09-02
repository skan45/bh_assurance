import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import TopNavigation from "./components/TopNavigation";
import SubHeader from "./components/SubHeader";
import Sidebar from "./components/Sidebar";
import ChatInterface from "./components/ChatInterface";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <div className="h-screen flex flex-col bg-background">
          {/* Top bar */}
          <TopNavigation />
          
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

export default App;
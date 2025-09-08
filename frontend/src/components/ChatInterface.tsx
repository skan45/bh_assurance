import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import ReactMarkdown from "react-markdown"; 
import { Card, CardContent } from "@/components/ui/card";
import { Send, FileText, Coins, AlertTriangle, ThumbsUp, ThumbsDown } from "lucide-react";
import { useUser } from "@/context/UserContext";
import { useLanguage } from "@/context/LanguageContext";

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  feedback?: 'like' | 'dislike' | null;
}

const ChatInterface = () => {
  const { chatId } = useParams<{ chatId: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string | null>(chatId || null);
  const { user } = useUser();
  const { language } = useLanguage();
  const token = localStorage.getItem('auth_token');

  const optionCards = [
    {
      icon: FileText,
      title: language === "fr" ? "Garanties & exclusions" : "التغطيات والاستثناءات",
      description: language === "fr" 
        ? "Consultez les garanties incluses, leurs capitaux assurés et les exclusions" 
        : "اطلع على التغطيات المشمولة والمبالغ المؤمن عليها والاستثناءات"
    },
    {
      icon: AlertTriangle,
      title: language === "fr" ? "Sinistres" : "المطالبات",
      description: language === "fr" 
        ? "Suivez l'état de vos sinistres et vérifiez leur couverture" 
        : "تابع حالة مطالباتك وتحقق من التغطية"
    },
    {
      icon: Coins,
      title: language === "fr" ? "Paiements & contrats" : "المدفوعات والعقود",
      description: language === "fr" 
        ? "Vérifiez le statut de paiement et consultez vos contrats actifs" 
        : "تحقق من حالة المدفوعات واطلع على عقودك النشطة"
    },
  ];

  // Load chat history when chatId changes
  useEffect(() => {
    if (chatId) {
      setCurrentChatId(chatId);
      loadChatHistory(chatId);
    } else {
      setMessages([]);
      setCurrentChatId(null);
    }
  }, [chatId]);

  const decodeUnicodeString = (str: string) => {
    try {
      let decoded = str;
      if ((decoded.startsWith('"') && decoded.endsWith('"')) || 
          (decoded.startsWith("'") && decoded.endsWith("'"))) {
        decoded = decoded.slice(1, -1);
      }
      decoded = decoded.replace(/\\u[\dA-F]{4}/gi, (match) => String.fromCharCode(parseInt(match.replace(/\\u/g, ''), 16)));
      decoded = decoded.replace(/\\n/g, '\n').replace(/\\N/g, '\n').replace(/\n{3,}/g, '\n\n');
      return decoded;
    } catch {
      return str;
    }
  };

  const loadChatHistory = async (id: string) => {
    setIsLoadingHistory(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/history/chat/${id}/conversations`, {
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to load chat history");
      const data = await res.json();
      const transformedMessages: Message[] = [];
      data.conversations?.forEach((conv: any) => {
        if (conv.query) transformedMessages.push({ id: `user-${conv.id}`, type: 'user', content: decodeUnicodeString(conv.query), timestamp: new Date(conv.timestamp), feedback: null });
        if (conv.response) transformedMessages.push({ id: `assistant-${conv.id}`, type: 'assistant', content: decodeUnicodeString(conv.response), timestamp: new Date(conv.timestamp), feedback: conv.feedback || null });
      });
      setMessages(transformedMessages);
    } catch {
      setMessages([]);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;
    const userMessage: Message = { id: Date.now().toString(), type: "user", content, timestamp: new Date(), feedback: null };
    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    try {
      const body: any = { query: content };
      if (currentChatId) body.chat_id = currentChatId;
      const res = await fetch(`${import.meta.env.VITE_API_URL}/query`, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` }, body: JSON.stringify(body) });
      const data = await res.json();
      if (data.chat_id && !currentChatId) setCurrentChatId(data.chat_id);
      const fullResponse = data.response || (language === "fr" ? "Je suis là pour vous aider. Pouvez-vous reformuler votre question ?" : "أنا هنا لمساعدتك. هل يمكنك إعادة صياغة سؤالك؟");

      const assistantMessage: Message = { id: (Date.now() + 1).toString(), type: "assistant", content: "", timestamp: new Date(), feedback: null };
      setMessages(prev => [...prev, assistantMessage]);

      let index = 0;
      const interval = setInterval(() => {
        index++;
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1].content = fullResponse.slice(0, index);
          return updated;
        });
        if (index >= fullResponse.length) clearInterval(interval);
      }, 20);

    } catch {
      const assistantMessage: Message = { id: (Date.now() + 1).toString(), type: "assistant", content: language === "fr" ? "Une erreur est survenue. Veuillez réessayer." : "حدث خطأ. يرجى المحاولة مرة أخرى.", timestamp: new Date(), feedback: null };
      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleFeedback = async (messageId: string, feedbackType: 'like' | 'dislike') => {
    const currentMessage = messages.find(msg => msg.id === messageId);
    const newFeedback = currentMessage?.feedback === feedbackType ? null : feedbackType;
    setMessages(prev => prev.map(msg => msg.id === messageId ? { ...msg, feedback: newFeedback } : msg));

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ message_id: messageId, chat_id: currentChatId, feedback: newFeedback }),
      });
      if (!response.ok) setMessages(prev => prev.map(msg => msg.id === messageId ? { ...msg, feedback: currentMessage?.feedback || null } : msg));
    } catch {
      setMessages(prev => prev.map(msg => msg.id === messageId ? { ...msg, feedback: currentMessage?.feedback || null } : msg));
    }
  };

  const handleCardClick = (title: string) => {
    handleSendMessage(language === "fr" ? `Je souhaite obtenir des informations sur: ${title}` : `أود الحصول على معلومات حول: ${title}`);
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoadingHistory ? (
          <div className="max-w-4xl mx-auto flex justify-center items-center h-full">
            <div className="text-center text-muted-foreground">
              {language === "fr" ? "Chargement de la conversation..." : "جارٍ تحميل المحادثة..."}
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
             <h1 className="text-2xl font-bold text-foreground mb-2">
  {!user 
    ? (language === "fr" ? "Chargement..." : "جارٍ التحميل...") 
    : user.full_name 
      ? (language === "fr" 
          ? `Bonjour ${user.full_name} 👋` 
          : ` 👋 ${user.full_name} مرحبا `)  // <-- name first for Arabic
      : (language === "fr" ? "Bonjour visiteur 👋" : "زائر مرحبا 👋") // optional: visitor case
  }
</h1>
              <p className="text-muted-foreground">
                {language === "fr" ? "Comment je peux vous assister aujourd'hui ?" : "كيف يمكنني مساعدتك اليوم؟"}
              </p>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {optionCards.map((card, index) => (
                <Card key={index} className="cursor-pointer hover:shadow-md transition-shadow border border-border" onClick={() => handleCardClick(card.title)}>
                  <CardContent className="p-6 text-center">
                    <card.icon className="h-12 w-12 mx-auto mb-4 text-slate-800" />
                    <h3 className="font-semibold text-foreground mb-2">{card.title}</h3>
                    <p className="text-sm text-muted-foreground">{card.description}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`flex items-start gap-3 max-w-lg ${message.type === "user" ? "flex-row-reverse" : ""}`}>
                  {message.type === "assistant" && <img src="/personna.png" alt="BH Hub" className="h-8 w-8 mt-1" />}
                  <div className="flex flex-col">
                    <div className={`rounded-lg px-4 py-3 ${message.type === "user" ? "bg-chat-user-bg text-foreground" : "bg-card border border-border text-foreground"}`}>
                      {message.type === "assistant" ? (
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>
                      ) : (
                        <div className="whitespace-pre-line">{message.content}</div>
                      )}
                    </div>
                    {message.type === "assistant" && message.content && (
                      <div className="flex gap-1 mt-2 ml-2">
                        <Button variant="ghost" size="sm" className={`h-8 w-8 p-0 transition-all ${message.feedback === 'like' ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'text-gray-500 hover:text-green-600 hover:bg-green-50'}`} onClick={() => handleFeedback(message.id, 'like')}>
                          <ThumbsUp className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" className={`h-8 w-8 p-0 transition-all ${message.feedback === 'dislike' ? 'bg-red-100 text-red-700 hover:bg-red-200' : 'text-gray-500 hover:text-red-600 hover:bg-red-50'}`} onClick={() => handleFeedback(message.id, 'dislike')}>
                          <ThumbsDown className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex items-start gap-3 max-w-lg">
                  <img src="/personna.png" alt="BH Hub" className="h-8 w-8 mt-1" />
                  <div className="bg-card border border-border rounded-lg px-4 py-3">
                    <div className="text-muted-foreground animate-pulse">
                      {language === "fr" ? "Réponse en cours..." : "جارٍ الرد..."}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="border-t border-border p-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-3">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={language === "fr" ? "Vous avez une question ?" : "هل لديك سؤال؟"}
              className="flex-1"
              onKeyPress={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSendMessage(inputValue); } }}
            />
            <Button onClick={() => handleSendMessage(inputValue)} className="bg-slate-800 hover:bg-slate-900 text-white" size="icon">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

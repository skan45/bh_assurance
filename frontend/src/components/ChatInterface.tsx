import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import ReactMarkdown from "react-markdown"; 
import { Card, CardContent } from "@/components/ui/card";
import { Send, FileText, Coins, AlertTriangle } from "lucide-react";
import { useUser } from "@/context/UserContext";

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const { user } = useUser();

  const optionCards = [
    { icon: FileText, title: "Garanties & exclusions", description: "Consultez les garanties incluses, leurs capitaux assurés et les exclusions" },
    { icon: AlertTriangle, title: "Sinistres", description: "Suivez l’état de vos sinistres et vérifiez leur couverture" },
    { icon: Coins, title: "Paiements & contrats", description: "Vérifiez le statut de paiement et consultez vos contrats actifs" },
  ];

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    try {
      const token = import.meta.env.VITE_CHAT_API_TOKEN;

      const body: any = { query: content };
      if (currentChatId) body.chat_id = currentChatId;

      const res = await fetch(`${import.meta.env.VITE_API_URL}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (data.chat_id && !currentChatId) {
        setCurrentChatId(data.chat_id);
      }

      const fullResponse = data.response || "Je suis là pour vous aider. Pouvez-vous reformuler votre question ?";

      // Add placeholder assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: "",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Typing effect
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

    } catch (error) {
      console.error("Error sending message:", error);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: "Une erreur est survenue. Veuillez réessayer.",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleCardClick = (title: string) => {
    handleSendMessage(`Je souhaite obtenir des informations sur: ${title}`);
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold text-foreground mb-2">
                Bonjour {user?.username || "Loading..."} 👋
              </h1>
              <p className="text-muted-foreground">Comment je peux vous assister aujourd'hui ?</p>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              {optionCards.map((card, index) => (
                <Card
                  key={index}
                  className="cursor-pointer hover:shadow-md transition-shadow border border-border"
                  onClick={() => handleCardClick(card.title)}
                >
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
              <div
                key={message.id}
                className={`flex ${message.type === "user" ? "justify-end" : "justify-start"}`}
              >
                <div className={`flex items-start gap-3 max-w-lg ${message.type === "user" ? "flex-row-reverse" : ""}`}>
                  {message.type === "assistant" && (
                    <img src="./personna.png" alt="BH Hub" className="h-8 w-8 mt-1" />
                  )}
                  <div className={`rounded-lg px-4 py-3 ${message.type === "user" ? "bg-chat-user-bg text-foreground" : "bg-card border border-border text-foreground"}`}>
                    {message.type === "assistant" ? (
                      <div className="prose prose-sm max-w-none">
                      <ReactMarkdown >
                        {message.content}
                      </ReactMarkdown>
                      </div>
                    ) : (
                      <div className="whitespace-pre-line">{message.content}</div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="flex items-start gap-3 max-w-lg">
                  <img src="./personna.png" alt="BH Hub" className="h-8 w-8 mt-1" />
                  <div className="bg-card border border-border rounded-lg px-4 py-3">
                    <div className="text-muted-foreground">Réponse en cours...</div>
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
              placeholder="Vous avez une question ?"
              className="flex-1"
              onKeyPress={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(inputValue);
                }
              }}
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

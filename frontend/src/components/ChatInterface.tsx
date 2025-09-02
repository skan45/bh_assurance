import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import ReactMarkdown from "react-markdown"; 
import { Card, CardContent } from "@/components/ui/card";
import { Send, FileText, Coins, AlertTriangle, ThumbsUp, ThumbsDown } from "lucide-react";
import { useUser } from "@/context/UserContext";

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
  const token = localStorage.getItem('auth_token');

  const optionCards = [
    { icon: FileText, title: "Garanties & exclusions", description: "Consultez les garanties incluses, leurs capitaux assurés et les exclusions" },
    { icon: AlertTriangle, title: "Sinistres", description: "Suivez l'état de vos sinistres et vérifiez leur couverture" },
    { icon: Coins, title: "Paiements & contrats", description: "Vérifiez le statut de paiement et consultez vos contrats actifs" },
  ];

  // Load chat history when chatId changes
  useEffect(() => {
    console.log("ChatId changed:", chatId); // Debug log
    if (chatId) {
      setCurrentChatId(chatId);
      loadChatHistory(chatId);
    } else {
      // Clear everything for new chat
      console.log("Clearing messages for new chat"); // Debug log
      setMessages([]);
      setCurrentChatId(null);
    }
  }, [chatId]);

  // Helper function to decode Unicode escape sequences and handle newlines
  const decodeUnicodeString = (str: string): string => {
    try {
      let decoded = str;
      
      // Remove surrounding quotes if present
      if ((decoded.startsWith('"') && decoded.endsWith('"')) || 
          (decoded.startsWith("'") && decoded.endsWith("'"))) {
        decoded = decoded.slice(1, -1);
      }
      
      // Replace Unicode escape sequences with actual characters
      decoded = decoded.replace(/\\u[\dA-F]{4}/gi, (match) => {
        return String.fromCharCode(parseInt(match.replace(/\\u/g, ''), 16));
      });
      
      // Replace escaped newlines with actual newlines
      decoded = decoded.replace(/\\n/g, '\n');
      decoded = decoded.replace(/\\N/g, '\n');
      
      // Replace multiple consecutive newlines with double newlines for better spacing
      decoded = decoded.replace(/\n{3,}/g, '\n\n');
      
      return decoded;
    } catch (error) {
      console.warn("Error decoding Unicode string:", error);
      return str;
    }
  };

  const loadChatHistory = async (id: string) => {
    setIsLoadingHistory(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/history/chat/${id}/conversations`, {
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        console.error(`Failed to load chat history: ${res.status} ${res.statusText}`);
        throw new Error("Failed to load chat history");
      }

      const data = await res.json();
      console.log("Chat history data:", data); // Debug log
      
      // Transform API response to match Message interface
      // Each conversation has query and response, so we need to create 2 messages per conversation
      const transformedMessages: Message[] = [];
      
      if (data.conversations && Array.isArray(data.conversations)) {
        data.conversations.forEach((conv: any) => {
          // Add user message (query)
          if (conv.query) {
            transformedMessages.push({
              id: `user-${conv.id}`,
              type: 'user',
              content: decodeUnicodeString(conv.query),
              timestamp: new Date(conv.timestamp),
              feedback: null
            });
          }
          
          // Add assistant message (response)
          if (conv.response) {
            transformedMessages.push({
              id: `assistant-${conv.id}`,
              type: 'assistant',
              content: decodeUnicodeString(conv.response),
              timestamp: new Date(conv.timestamp),
              feedback: conv.feedback || null // Load existing feedback if available
            });
          }
        });
      }

      setMessages(transformedMessages);
    } catch (error) {
      console.error("Error loading chat history:", error);
      // Don't redirect on error, just show empty chat
      setMessages([]);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content,
      timestamp: new Date(),
      feedback: null,
    };
    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    try {
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
        feedback: null,
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
        feedback: null,
      };
      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleFeedback = async (messageId: string, feedbackType: 'like' | 'dislike') => {
    // Get current feedback state for this message
    const currentMessage = messages.find(msg => msg.id === messageId);
    const newFeedback = currentMessage?.feedback === feedbackType ? null : feedbackType;

    // Update local state immediately for better UX
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, feedback: newFeedback }
          : msg
      )
    );

    try {
      // Send feedback to backend
      const response = await fetch(`${import.meta.env.VITE_API_URL}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          message_id: messageId,
          chat_id: currentChatId,
          feedback: newFeedback, // Send null if toggling off, or the new feedback type
        }),
      });

      if (!response.ok) {
        console.error("Failed to send feedback");
        // Revert the optimistic update if the request failed
        setMessages(prev => 
          prev.map(msg => 
            msg.id === messageId 
              ? { ...msg, feedback: currentMessage?.feedback || null }
              : msg
          )
        );
      }
    } catch (error) {
      console.error("Error sending feedback:", error);
      // Revert the optimistic update if the request failed
      setMessages(prev => 
        prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, feedback: currentMessage?.feedback || null }
            : msg
        )
      );
    }
  };

  const handleCardClick = (title: string) => {
    handleSendMessage(`Je souhaite obtenir des informations sur: ${title}`);
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoadingHistory ? (
          <div className="max-w-4xl mx-auto flex justify-center items-center h-full">
            <div className="text-center text-muted-foreground">
              Chargement de la conversation...
            </div>
          </div>
        ) : messages.length === 0 ? (
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
                    <img src="/personna.png" alt="BH Hub" className="h-8 w-8 mt-1" />
                  )}
                  <div className="flex flex-col">
                    <div className={`rounded-lg px-4 py-3 ${message.type === "user" ? "bg-chat-user-bg text-foreground" : "bg-card border border-border text-foreground"}`}>
                      {message.type === "assistant" ? (
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown>
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <div className="whitespace-pre-line">{message.content}</div>
                      )}
                    </div>
                    
                    {/* Feedback buttons for assistant messages only */}
                    {message.type === "assistant" && message.content && (
                      <div className="flex gap-1 mt-2 ml-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className={`h-8 w-8 p-0 transition-all ${
                            message.feedback === 'like' 
                              ? 'bg-green-100 text-green-700 hover:bg-green-200' 
                              : 'text-gray-500 hover:text-green-600 hover:bg-green-50'
                          }`}
                          onClick={() => handleFeedback(message.id, 'like')}
                        >
                          <ThumbsUp className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className={`h-8 w-8 p-0 transition-all ${
                            message.feedback === 'dislike' 
                              ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                              : 'text-gray-500 hover:text-red-600 hover:bg-red-50'
                          }`}
                          onClick={() => handleFeedback(message.id, 'dislike')}
                        >
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
          Réponse en cours...
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
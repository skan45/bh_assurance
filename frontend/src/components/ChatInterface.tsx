import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Send, FileText, Coins, MapPin, Shield, CheckCircle } from "lucide-react";


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

  const optionCards = [
    {
      icon: FileText,
      title: "Consultation des garanties contractuelles",
      description: "Consultez vos garanties et conditions"
    },
    {
      icon: Coins,
      title: "Suivi et gestion des données financières", 
      description: "Gérez vos paiements et factures"
    },
    {
      icon: MapPin,
      title: "Localisation et orientation vers les agences",
      description: "Trouvez l'agence la plus proche"
    }
  ];

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    // Simulate assistant response
    setTimeout(() => {
      const responses: { [key: string]: string } = {
        "quel est mon dernier sinistre déclaré": "Le sinistre numéro 20234000127, rattaché au contrat 202210500349, a été enregistré le 15 mars 2024. Il s'agit d'un dégât des eaux dans votre résidence principale.",
        "quelles garanties couvrent ce sinistre": "Ce sinistre est couvert par les garanties suivantes dans votre contrat MULTIRISQUE HABITATION :\n\n✅ Dommages incendie et explosion\n✅ Frais de sauvetage et de déblai\n✅ Responsabilité civile habitation\n\nNote: Les exclusions sont détaillées dans vos conditions générales.",
        "est-ce que j'ai des paiements en retard": "Tous vos contrats sont à jour. Votre prochain prélèvement de 145,60€ est prévu le 15 du mois prochain pour votre contrat automobile."
      };

      const response = responses[content.toLowerCase()] || "Je suis là pour vous aider. Pouvez-vous reformuler votre question ?";

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 2000);
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
            {/* Welcome Message */}
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold text-foreground mb-2">
                Bonjour Mohamed 👋
              </h1>
              <p className="text-muted-foreground">
                Comment je peux vous assister aujourd'hui ?
              </p>
            </div>

            {/* Option Cards */}
            <div className="grid gap-4 md:grid-cols-3">
              {optionCards.map((card, index) => (
                <Card
                  key={index}
                  className="cursor-pointer hover:shadow-md transition-shadow border border-border"
                  onClick={() => handleCardClick(card.title)}
                >
                  <CardContent className="p-6 text-center">
                    <card.icon className="h-12 w-12 mx-auto mb-4 text-bh-blue" />
                    <h3 className="font-semibold text-foreground mb-2">
                      {card.title}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {card.description}
                    </p>
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
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex items-start gap-3 max-w-lg ${message.type === 'user' ? 'flex-row-reverse' : ''}`}>
                  {message.type === 'assistant' && (
                    <img src="./personna.png" alt="BH Hub" className="h-8 w-8 mt-1" />
                  )}
                  <div
                    className={`rounded-lg px-4 py-3 ${
                      message.type === 'user'
                        ? 'bg-chat-user-bg text-foreground'
                        : 'bg-card border border-border text-foreground'
                    }`}
                  >
                    <div className="whitespace-pre-line">{message.content}</div>
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
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(inputValue);
                }
              }}
            />
            <Button
              onClick={() => handleSendMessage(inputValue)}
              className="bg-bh-blue hover:bg-bh-blue-dark"
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
import { useState, useEffect } from "react";

interface ChatRoom {
  chat_id: number;
  chat_name: string;
}

const Sidebar = () => {
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([]);
  const token = import.meta.env.VITE_CHAT_API_TOKEN;

  useEffect(() => {
    const fetchChatRooms = async () => {
      try {
        const res = await fetch(`${import.meta.env.VITE_API_URL}/history/user_chats`, {
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
        });

        if (!res.ok) throw new Error("Failed to fetch chat rooms");

        const data = await res.json();
        setChatRooms(data.chats);
      } catch (error) {
        console.error("Error fetching chat rooms:", error);
      }
    };

    fetchChatRooms();
  }, []);

  return (
    <aside className="w-80 bg-sidebar-bg border border-border h-full flex flex-col m-2 shadow-sm">
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {chatRooms.length === 0 ? (
          <div className="text-sm text-muted-foreground">Aucune conversation</div>
        ) : (
          chatRooms.map((chat) => (
            <div
              key={chat.chat_id}
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-accent cursor-pointer transition-colors"
            >
              <span className="text-sm text-foreground">{chat.chat_name}</span>
            </div>
          ))
        )}
      </div>
    </aside>
  );
};

export default Sidebar;

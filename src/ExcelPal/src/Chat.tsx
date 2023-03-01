import React, { useState, useEffect, useRef } from "react";
import "./Chat.css";

const socket = new WebSocket("ws://localhost:3001/ws");

function Chat(): JSX.Element {
  const [messages, setMessages] = useState<
    { id: number; text: string; isFromServer: boolean }[]
  >([]);
  const [newMessage, setNewMessage] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    socket.onmessage = (event) => {
      const messageData = {
        id: messages.length,
        text: event.data,
        isFromServer: true,
      };
      setMessages((prevMessages) => [...prevMessages, messageData]);
    };
  }, [messages.length]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollTop = messagesEndRef.current.scrollHeight;
    }
  }, [messages]);

  const handleNewMessageChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setNewMessage(event.target.value);
  };

  const handleSendMessage = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const messageData = {
      id: messages.length,
      text: newMessage,
      isFromServer: false,
    };
    setMessages((prevMessages) => [...prevMessages, messageData]);
    socket.send(newMessage);
    setNewMessage("");
  };

  return (
    <div className="chat-container">
      <div className="messages-container">
        {messages.map((messageData) => (
          <div
            key={messageData.id}
            className={`balloon ${
              messageData.isFromServer ? "server" : "sender"
            }`}
          >
            {messageData.text}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <form className="input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={newMessage}
          onChange={handleNewMessageChange}
          placeholder="Type your message here..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}

export default Chat;

import React, { useState, useRef, useEffect } from "react";
import ApartmentCard from "./ApartmentCard";

interface Apartment {
    id: string;
    city: string;
    rooms: number;
    surface_m2: number;
    furnished: boolean;
    rent_cc_eur: number;
    availability_date: string;
    energy_label: string;
    postal_code: string;
    content: string;
}

interface Message {
    id: string;
    sender: 'user' | 'ai';
    content: string;
    timestamp: Date;
    isStreaming?: boolean;
    apartments?: Apartment[];
}

export default function SemanticSearch() {
    const [input, setInput] = useState("");
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            sender: 'ai',
            content: "Bonjour ! Je suis Sarah, votre conseillère en logement chez ECLA. 🏠\n\nJe suis là pour vous accompagner dans votre recherche d'appartement. Dites-moi ce que vous recherchez (ville, budget, type de logement) et je vous trouve les meilleures options !",
            timestamp: new Date(),
        }
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const messagesRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (messagesRef.current) {
            messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
        }
    }, [messages]);

    useEffect(() => {
        if (!isLoading && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isLoading]);

    const handleSendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            sender: 'user',
            content: input.trim(),
            timestamp: new Date(),
        };

        const aiMessage: Message = {
            id: (Date.now() + 1).toString(),
            sender: 'ai',
            content: '',
            timestamp: new Date(),
            isStreaming: true,
        };

        setMessages(prev => [...prev, userMessage, aiMessage]);
        setInput("");
        setIsLoading(true);

        try {
            // URL adaptable : local en dev, Railway en production
            const apiUrl = import.meta.env.DEV
                ? "http://localhost:8000"
                : "https://chatiaecla-production.up.railway.app";

            console.log("🌐 Mode DEV:", import.meta.env.DEV);
            console.log("🎯 URL utilisée:", apiUrl);

            // Construire l'historique conversationnel (exclure le message en cours)
            const conversationHistory = messages
                .filter(msg => msg.sender !== 'ai' || !msg.isStreaming)
                .slice(-6)  // Garder les 6 derniers messages (3 échanges)
                .map(msg => ({
                    role: msg.sender === 'user' ? 'user' : 'assistant',
                    content: msg.content
                }));

            const response = await fetch(`${apiUrl}/search`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    query: userMessage.content,
                    summarize: true,
                    conversation_history: conversationHistory,
                }),
            });

            if (!response.ok) {
                throw new Error(`Erreur ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            const fullResponse = data.answer || "Désolé, je n'ai pas pu traiter votre demande.";

            // D'abord afficher le texte avec effet de typing
            await simulateStreaming(aiMessage.id, fullResponse);

            // Puis afficher les appartements progressivement après le texte
            if (data.has_apartments && data.apartments) {
                // Petit délai avant d'afficher les cards
                await new Promise(resolve => setTimeout(resolve, 200));

                setMessages(prev => prev.map(msg =>
                    msg.id === aiMessage.id
                        ? { ...msg, apartments: data.apartments }
                        : msg
                ));
            }

        } catch (error) {
            const errorMessage = error instanceof Error
                ? `Erreur: ${error.message}`
                : "Une erreur inattendue s'est produite.";

            await simulateStreaming(aiMessage.id, errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const simulateStreaming = async (messageId: string, fullText: string) => {
        // Effet typing caractère par caractère (comme ChatGPT)
        let currentText = '';

        for (let i = 0; i < fullText.length; i++) {
            currentText += fullText[i];

            setMessages(prev => prev.map(msg =>
                msg.id === messageId
                    ? { ...msg, content: currentText, isStreaming: i < fullText.length - 1 }
                    : msg
            ));

            // Délai variable : plus rapide pour les espaces, plus lent pour la ponctuation
            let delay = 15;  // Réduit de 20 à 15ms
            if (fullText[i] === ' ') delay = 20;  // Réduit de 30 à 20ms
            if (['.', '!', '?'].includes(fullText[i])) delay = 50;  // Réduit de 100 à 80ms
            if ([',', ';', ':'].includes(fullText[i])) delay = 10;  // Réduit de 50 à 40ms

            await new Promise(resolve => setTimeout(resolve, delay));
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const formatTime = (date: Date) => {
        return date.toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="chat-container">
            <div className="chat-header">
                <h1>Votre interlocuteur privilégié pour votre recherche d'appartement</h1>
                {/* <p>Recherche sémantique dans vos documents</p> */}
            </div>

            <div className="chat-messages" ref={messagesRef}>
                {messages.map((message) => (
                    <React.Fragment key={message.id}>
                        {message.sender === 'ai' ? (
                            <div className="message-wrapper-ai">
                                <div className="message-row-ai">
                                    <div className="message-avatar ai">S</div>
                                    <div className="message-content ai">
                                        <p>
                                            {message.content}
                                            {message.isStreaming && (
                                                <span className="typing-indicator"></span>
                                            )}
                                        </p>
                                    </div>
                                </div>
                                <div className="message-time-ai">
                                    {formatTime(message.timestamp)}
                                </div>
                            </div>
                        ) : (
                            <div className="message-wrapper-user">
                                <div className="message-row-user">
                                    <div className="message-content user">
                                        <p>{message.content}</p>
                                    </div>
                                    <div className="message-avatar user">U</div>
                                </div>
                                <div className="message-time-user">
                                    {formatTime(message.timestamp)}
                                </div>
                            </div>
                        )}

                        {message.apartments && message.apartments.length > 0 && (
                            <div className="apartments-grid">
                                {message.apartments.map((apt) => (
                                    <ApartmentCard key={apt.id} apartment={apt} />
                                ))}
                            </div>
                        )}
                    </React.Fragment>
                ))}
            </div>

            <div className="chat-input">
                <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Tapez votre message..."
                    disabled={isLoading}
                />
                <button
                    onClick={handleSendMessage}
                    disabled={!input.trim() || isLoading}
                >
                    {isLoading ? (
                        <div className="loading-spinner"></div>
                    ) : (
                        "Envoyer"
                    )}
                </button>
            </div>
        </div>
    );
}

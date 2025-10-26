import React, { useState, useRef, useEffect } from "react";
import ApartmentCard from "./ApartmentCard";
import UpsellOptionsModal from "./UpsellOptionsModal";
import BookingSummary from "./BookingSummary";
import type { QuickReply } from '../types/quickReply';

interface Apartment {
    id: string;
    typologie_id?: string;
    city: string;
    rooms: number;
    surface_m2: number;
    surface_min?: number;
    surface_max?: number;
    furnished: boolean;
    rent_cc_eur: number;
    availability_date: string;
    energy_label: string;
    postal_code: string;
    floor?: number;
    orientation?: string;
    bed_size?: number;
    has_ac?: boolean;
    application_fee?: number;
    deposit_months?: number;
    is_typologie?: boolean;
    content: string;
}

interface UpsellOptions {
    tv: boolean;
    packLinge: boolean;
    parkingIndoor: boolean;
    parkingOutdoor: boolean;
}

interface BookingSummary {
    typologie: Apartment;
    baseRent: number;
    floorSupplement: number;
    optionsCost: number;
    totalRent: number;
    applicationFee: number;
    deposit: number;
    selectedOptions: string[];
}

interface Message {
    id: string;
    sender: 'user' | 'ai';
    content: string;
    timestamp: Date;
    isStreaming?: boolean;
    apartments?: Apartment[];
    residences?: string[];
    quickReplies?: QuickReply[]; // Boutons de réponse rapide
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
    const [selectedTypologie, setSelectedTypologie] = useState<Apartment | null>(null);
    const [upsellOptions, setUpsellOptions] = useState<UpsellOptions>({
        tv: false,
        packLinge: false,
        parkingIndoor: false,
        parkingOutdoor: false
    });
    const [bookingSummary, setBookingSummary] = useState<BookingSummary | null>(null);
    const [showUpsellModal, setShowUpsellModal] = useState(false);
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
        console.log('🚀🚀🚀 DEBUT handleSendMessage 🚀🚀🚀');
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
            console.log('✅✅✅ DONNÉES REÇUES ✅✅✅');
            console.log('[DEBUG] Backend response:', data);
            console.log('[DEBUG] Quick replies dans response:', data.quick_replies);
            console.log('[DEBUG] Has apartments:', data.has_apartments);
            console.log('[DEBUG] Type de quick_replies:', typeof data.quick_replies, Array.isArray(data.quick_replies));
            const fullResponse = data.answer || "Désolé, je n'ai pas pu traiter votre demande.";

            // D'abord afficher le texte avec effet de typing
            await simulateStreaming(aiMessage.id, fullResponse);

            // Puis afficher les appartements ou résidences après le texte
            if (data.has_apartments && data.apartments && data.apartments.length > 0) {
                // Petit délai avant d'afficher les cards
                await new Promise(resolve => setTimeout(resolve, 200));

                setMessages(prev => prev.map(msg =>
                    msg.id === aiMessage.id
                        ? { ...msg, apartments: data.apartments }
                        : msg
                ));
            } else if (data.quick_replies && data.quick_replies.length > 0) {
                // Afficher les boutons de réponse rapide
                console.log('[DEBUG] Affichage des quick replies:', data.quick_replies);
                await new Promise(resolve => setTimeout(resolve, 200));

                setMessages(prev => prev.map(msg =>
                    msg.id === aiMessage.id
                        ? { ...msg, quickReplies: data.quick_replies }
                        : msg
                ));
                console.log('[DEBUG] Messages mis à jour avec quick replies');
            } else {
                console.log('[DEBUG] Pas de quick replies à afficher. has_apartments:', data.has_apartments, 'quick_replies:', data.quick_replies);
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

    // Handlers pour le système de réservation
    const handleReserveTypologie = (typologie: Apartment) => {
        console.log('[SemanticSearch] handleReserveTypologie called for:', typologie.id);
        setSelectedTypologie(typologie);
        console.log('[SemanticSearch] Setting showUpsellModal to true');
        setShowUpsellModal(true);
    };

    const handleValidateOptions = (options: UpsellOptions, totalRent: number) => {
        if (!selectedTypologie) return;

        const calculateFloorSupplement = (floor: number): number => {
            if (floor === 0) return 0;
            if (floor <= 2) return 30;
            if (floor <= 4) return 50;
            if (floor <= 6) return 80;
            return 100;
        };

        const calculateOptionsCost = (opts: UpsellOptions): number => {
            let cost = 0;
            if (opts.tv) cost += 40;
            if (opts.packLinge) cost += 30;
            if (opts.parkingIndoor) cost += 50;
            if (opts.parkingOutdoor) cost += 30;
            return cost;
        };

        const selectedOptionsLabels: string[] = [];
        if (options.tv) selectedOptionsLabels.push("Télévision (+40€/mois)");
        if (options.packLinge) selectedOptionsLabels.push("Pack linge (+30€/mois)");
        if (options.parkingIndoor) selectedOptionsLabels.push("Place de parking sous-sol (+50€/mois)");
        if (options.parkingOutdoor) selectedOptionsLabels.push("Place de parking extérieur (+30€/mois)");

        const floorSupplement = calculateFloorSupplement(selectedTypologie.floor || 0);
        const optionsCost = calculateOptionsCost(options);

        const summary: BookingSummary = {
            typologie: selectedTypologie,
            baseRent: selectedTypologie.rent_cc_eur,
            floorSupplement,
            optionsCost,
            totalRent,
            applicationFee: selectedTypologie.application_fee || 100,
            deposit: selectedTypologie.rent_cc_eur * (selectedTypologie.deposit_months || 1),
            selectedOptions: selectedOptionsLabels
        };

        setUpsellOptions(options);
        setBookingSummary(summary);
        setShowUpsellModal(false);

        // Ajouter le récapitulatif comme message système
        const summaryMessage: Message = {
            id: Date.now().toString(),
            sender: 'ai',
            content: '',
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, summaryMessage]);
    };

    const handleModifyOptions = () => {
        setShowUpsellModal(true);
    };

    const handleContinueChat = () => {
        setBookingSummary(null);
        setSelectedTypologie(null);
        if (inputRef.current) {
            inputRef.current.focus();
        }
    };

    const handleFinalize = () => {
        alert("Fonctionnalité de finalisation à venir ! (POC)");
    };

    const handleQuickReplyClick = async (reply: QuickReply) => {
        console.log('[DEBUG] Quick reply clicked:', reply);

        // Créer un message utilisateur avec le label cliqué
        const userMessage: Message = {
            id: Date.now().toString(),
            sender: 'user',
            content: reply.label,
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
        setIsLoading(true);

        try {
            const apiUrl = import.meta.env.DEV
                ? "http://localhost:8000"
                : "https://chatiaecla-production.up.railway.app";

            console.log('[DEBUG] Envoi de la requête vers:', `${apiUrl}/search`);

            const conversationHistory = messages
                .filter(msg => msg.sender !== 'ai' || !msg.isStreaming)
                .slice(-6)
                .map(msg => ({
                    role: msg.sender === 'user' ? 'user' : 'assistant',
                    content: msg.content
                }));

            console.log('[DEBUG] Conversation history:', conversationHistory);

            const response = await fetch(`${apiUrl}/search`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    query: reply.value === 'flexible' ? "Je suis flexible sur la ville" : `Montre moi les typologies disponibles à ${reply.value}`,
                    summarize: true,
                    conversation_history: conversationHistory,
                    type: "appartement"
                }),
            });

            if (!response.ok) {
                throw new Error(`Erreur ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            const fullResponse = data.answer || "Désolé, je n'ai pas pu traiter votre demande.";

            await simulateStreaming(aiMessage.id, fullResponse);

            if (data.has_apartments && data.apartments) {
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

                        {/* DEBUG: Afficher l'état des quickReplies */}
                        {message.sender === 'ai' && (
                            <div style={{ fontSize: '10px', color: 'red', marginTop: '4px' }}>
                                DEBUG: quickReplies={message.quickReplies ? `[${message.quickReplies.length} boutons]` : 'undefined'}
                            </div>
                        )}

                        {/* Boutons de réponse rapide (Quick Replies) */}
                        {message.quickReplies && message.quickReplies.length > 0 && (
                            <div className="quick-replies-container">
                                {message.quickReplies.map((reply) => (
                                    <button
                                        key={reply.id}
                                        className="quick-reply-btn"
                                        onClick={() => handleQuickReplyClick(reply)}
                                        disabled={isLoading}
                                    >
                                        {reply.icon && <span className="quick-reply-icon">{reply.icon}</span>}
                                        <span className="quick-reply-label">{reply.label}</span>
                                    </button>
                                ))}
                            </div>
                        )}

                        {/* Cards des typologies */}
                        {message.apartments && message.apartments.length > 0 && (
                            <div className="apartments-grid">
                                {message.apartments.map((apt) => (
                                    <ApartmentCard
                                        key={apt.id}
                                        apartment={apt}
                                        onReserve={handleReserveTypologie}
                                    />
                                ))}
                            </div>
                        )}

                        {/* Afficher le BookingSummary si c'est le dernier message AI et qu'il existe */}
                        {message.sender === 'ai' &&
                            messages[messages.length - 1].id === message.id &&
                            bookingSummary && (
                                <BookingSummary
                                    summary={bookingSummary}
                                    onModifyOptions={handleModifyOptions}
                                    onContinueChat={handleContinueChat}
                                    onFinalize={handleFinalize}
                                />
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

            {/* Modal pour les options upsell */}
            {showUpsellModal && selectedTypologie && (
                <UpsellOptionsModal
                    typologie={selectedTypologie}
                    currentOptions={upsellOptions}
                    onValidate={handleValidateOptions}
                    onClose={() => {
                        console.log('[SemanticSearch] Closing modal');
                        setShowUpsellModal(false);
                    }}
                />
            )}
        </div>
    );
}

// Types pour les boutons de réponse rapide (Quick Replies)

export interface QuickReply {
    id: string;
    label: string;
    value: string;
    icon?: string;
}

export interface QuickReplySet {
    type: 'city' | 'budget' | 'living_type' | 'rooms' | 'custom';
    replies: QuickReply[];
}


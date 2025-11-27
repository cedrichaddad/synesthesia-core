export interface Song {
    id: string;
    title: string;
    artist: string;
    album?: string;
    bpm?: number;
    key?: string;
    genre?: string;
    coverUrl?: string;
    energy_level?: number; // 0-100
    coordinates?: string; // Added for UI compatibility
    reason?: string; // Added for UI compatibility
    vector?: number[]; // 5D Vector for Knob Locking
}

export interface KnobState {
    [key: string]: number; // 0-100
}

export enum SensorState {
    IDLE = 'IDLE',
    LISTENING = 'LISTENING',
    PROCESSING = 'PROCESSING',
    SUCCESS = 'SUCCESS',
    ERROR = 'ERROR'
}

export interface RecommendationPayload {
    current_song_id: string;
    knobs: KnobState;
}

export interface ApiError {
    message: string;
    code?: number;
}

export interface SearchResponse {
    song_id: string;
    metadata: {
        title: string;
        artist: string;
        genre: string;
        [key: string]: unknown;
    };
    vector: number[];
}

export interface RecommendResponse {
    songs: {
        id: string;
        title: string;
        artist: string;
        genre: string;
        coordinates?: string;
        reason?: string;
        [key: string]: unknown;
    }[];
    vector: number[];
}

export interface KnobDefinition {
    id: string;
    label: string;
    min: number;
    max: number;
    defaultValue: number;
    vector: number[];
    color: string;
}

export interface KnobConfig {
    knobs: KnobDefinition[];
}

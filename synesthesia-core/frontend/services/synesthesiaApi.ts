import { Song, SearchResponse, RecommendResponse, RecommendationPayload } from '../types';

const API_BASE = 'http://127.0.0.1:8000';

export const searchSongs = async (query: string): Promise<{ results: Song[] }> => {
    const res = await fetch(`${API_BASE}/search?query=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error('Nav Computer could not lock onto target.');
    const data: SearchResponse = await res.json();

    const song: Song = {
        id: data.song_id,
        title: data.metadata.title,
        artist: data.metadata.artist,
        genre: data.metadata.genre,
        coordinates: `VEC-[${data.vector.slice(0, 3).map(n => n.toFixed(3)).join(' | ')}]`,
        vector: data.vector
    };

    return { results: [song] };
};

export const getRecommendations = async (payload: RecommendationPayload): Promise<{ songs: Song[], vector: number[] }> => {
    // Transform knobs: Expects normalized values (-1.0 to 1.0) from caller
    const knobPayload = payload.knobs;

    const res = await fetch(`${API_BASE}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            current_song_id: payload.current_song_id,
            knobs: knobPayload
        })
    });

    if (!res.ok) {
        const errorText = await res.text();
        console.error('Recommend API error:', errorText);
        throw new Error('Hyperspace jump failed. Check targeting computer.');
    }

    const data: RecommendResponse = await res.json();

    const songs = data.songs.map((song, idx) => {
        // Generate coordinates from vector if available
        let coordinates = 'Unknown Sector';
        if (data.vector && data.vector.length >= 3) {
            const x = data.vector[0].toFixed(3);
            const y = data.vector[1].toFixed(3);
            const z = data.vector[2].toFixed(3);
            coordinates = `Sector ${x} | ${y} | ${z}`;
        } else if (song.id) {
            coordinates = `Sector ${song.id.substring(0, 4).toUpperCase()}-${song.id.substring(song.id.length - 2).toUpperCase()}`;
        }

        return {
            id: song.id,
            title: song.title,
            artist: song.artist,
            genre: song.genre,
            reason: song.reason || (idx === 0 ? 'Primary destination' : `Alternative route ${idx}`),
            coordinates: song.coordinates || coordinates,
            bpm: song.bpm as number | undefined,
            key: song.key as string | undefined,
            energy_level: song.energy_level as number | undefined,
            vector: song.vector as number[] | undefined
        };
    });

    return { songs, vector: data.vector };
};

export const identifyAudio = async (blob: Blob): Promise<{
    song: Song,
    metadata?: {
        processing_time: string,
        fingerprint_count: number
    },
    vector?: number[]
}> => {
    const formData = new FormData();
    formData.append('file', blob, 'recording.webm');

    const res = await fetch(`${API_BASE}/identify`, {
        method: 'POST',
        body: formData
    });

    if (!res.ok) throw new Error('Audio identification failed');

    const data = await res.json();

    return {
        song: {
            id: data.song_id,
            title: data.metadata.title,
            artist: data.metadata.artist,
            genre: data.metadata.genre,
            bpm: 120, // Mock data
            key: 'Cm', // Mock data
            energy_level: 85 // Mock data
        },
        metadata: {
            processing_time: data.metadata.processing_time,
            fingerprint_count: data.metadata.fingerprint_count
        },
        vector: data.vector // Assuming backend returns this now, or undefined
    };
};

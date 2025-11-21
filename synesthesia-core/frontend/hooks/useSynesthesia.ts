import { useState, useCallback, useRef } from 'react';
import { Song, KnobState, SensorState } from '../types';
import { searchSongs, identifyAudio, getRecommendations } from '../services/synesthesiaApi';

export const useSynesthesia = () => {
    const [currentSong, setCurrentSong] = useState<Song | null>(null);
    const [recommendations, setRecommendations] = useState<Song[]>([]);
    const [searchResults, setSearchResults] = useState<Song[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [sensorState, setSensorState] = useState<SensorState>(SensorState.IDLE);
    const [knobs, setKnobs] = useState<KnobState>({
        'ENERGY': 50,
        'ATMOSPHERE': 30,
        'DISTORTION': 0,
        'REVERB': 20,
        'BASS': 60,
        'TREBLE': 40,
    });

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);

    const updateKnob = useCallback((name: string, value: number) => {
        setKnobs(prev => {
            const newKnobs = { ...prev, [name]: value };
            return newKnobs;
        });
    }, []);

    const addKnob = useCallback((name: string) => {
        setKnobs(prev => {
            // Sanitize name: Uppercase, replace spaces with underscores, remove non-alphanumeric
            const key = name.toUpperCase().trim().replace(/\s+/g, '_').replace(/[^A-Z0-9_]/g, '');

            if (!key || prev[key] !== undefined) return prev;

            return { ...prev, [key]: 50 }; // Default to center position
        });
    }, []);

    // Trigger recommendation when a song is selected or knobs settle
    const fetchRecommendations = useCallback(async () => {
        if (!currentSong) return;
        try {
            const data = await getRecommendations({
                current_song_id: currentSong.id,
                knobs
            });
            setRecommendations(data.songs);
        } catch (error) {
            console.error("Recommendation failed", error);
        }
    }, [currentSong, knobs]);

    const handleSearch = useCallback(async (query: string) => {
        if (!query.trim()) {
            setSearchResults([]);
            return;
        }
        setIsSearching(true);
        try {
            const data = await searchSongs(query);
            setSearchResults(data.results);
        } finally {
            setIsSearching(false);
        }
    }, []);

    const startListening = useCallback(async () => {
        try {
            setSensorState(SensorState.LISTENING);
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            const chunks: BlobPart[] = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunks.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                setSensorState(SensorState.PROCESSING);
                const blob = new Blob(chunks, { type: 'audio/webm' });

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());

                try {
                    const result = await identifyAudio(blob);
                    setCurrentSong(result.song);
                    setSensorState(SensorState.SUCCESS);
                    setTimeout(() => setSensorState(SensorState.IDLE), 2000);
                } catch (err) {
                    console.error(err);
                    setSensorState(SensorState.ERROR);
                    setTimeout(() => setSensorState(SensorState.IDLE), 2000);
                }
            };

            mediaRecorder.start();

            // Auto-stop after 5 seconds
            setTimeout(() => {
                if (mediaRecorder.state !== 'inactive') {
                    mediaRecorder.stop();
                }
            }, 5000);

        } catch (err) {
            console.error("Mic permission denied or error", err);
            setSensorState(SensorState.ERROR);
            setTimeout(() => setSensorState(SensorState.IDLE), 2000);
        }
    }, []);

    return {
        currentSong,
        setCurrentSong,
        recommendations,
        searchResults,
        isSearching,
        sensorState,
        knobs,
        updateKnob,
        addKnob,
        handleSearch,
        startListening,
        fetchRecommendations
    };
};

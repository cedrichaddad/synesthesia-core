import { useState, useCallback, useRef, useEffect } from 'react';
import { Song, KnobState, SensorState, KnobConfig } from '../types';
import { searchSongs, identifyAudio, getRecommendations } from '../services/synesthesiaApi';

export const useSynesthesia = () => {
    const [currentSong, setCurrentSong] = useState<Song | null>(null);
    const [recommendations, setRecommendations] = useState<Song[]>([]);
    const [searchResults, setSearchResults] = useState<Song[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [sensorState, setSensorState] = useState<SensorState>(SensorState.IDLE);
    const DEFAULT_CONFIG: KnobConfig = {
        knobs: [
            { id: "energy", label: "Energy", min: -1.0, max: 1.0, defaultValue: 0.0, vector: [1.0, 0.0, 0.0, 0.0, 0.0], color: "#FF4D4D" },
            { id: "valence", label: "Happiness", min: -1.0, max: 1.0, defaultValue: 0.0, vector: [0.0, 1.0, 0.0, 0.0, 0.0], color: "#FFD700" },
            { id: "danceability", label: "Groove", min: -1.0, max: 1.0, defaultValue: 0.0, vector: [0.0, 0.0, 1.0, 0.0, 0.0], color: "#00FF00" },
            { id: "acousticness", label: "Organic", min: -1.0, max: 1.0, defaultValue: 0.0, vector: [0.0, 0.0, 0.0, 1.0, 0.0], color: "#00BFFF" },
            { id: "instrumentalness", label: "Vocals", min: -1.0, max: 1.0, defaultValue: 0.0, vector: [0.0, 0.0, 0.0, 0.0, -1.0], color: "#FF00FF" }
        ]
    };

    const [knobConfig, setKnobConfig] = useState<KnobConfig>(DEFAULT_CONFIG);

    const [knobs, setKnobs] = useState<KnobState>(() => {
        const initial: KnobState = {};
        DEFAULT_CONFIG.knobs.forEach(k => {
            const uiValue = ((k.defaultValue - k.min) / (k.max - k.min)) * 100;
            initial[k.id] = uiValue;
        });
        return initial;
    });

    // Optional: Still try to fetch updates if needed, but we have defaults now
    useEffect(() => {
        fetch('/config.json')
            .then(res => res.json())
            .then((config: KnobConfig) => {
                setKnobConfig(config);
            })
            .catch(err => console.warn("Using default config. Fetch failed:", err));
    }, []);

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

    // Lock Knobs to Song Vector
    useEffect(() => {
        if (currentSong && currentSong.vector && knobConfig) {
            const newKnobs: KnobState = { ...knobs };

            // Map vector [Energy, Valence, Dance, Acoustic, Inst] to Knobs
            // We need to know which knob maps to which vector index.
            // In config.json, each knob has a "vector" array (mask).
            // But here we want to set the knob VALUE based on the song's vector.
            // This implies the knob represents a specific dimension.

            // Heuristic: Match knob ID to vector index based on config
            // We iterate through config knobs and see which dimension they control (non-zero in vector mask)

            knobConfig.knobs.forEach(k => {
                // Find which index is non-zero in the knob's vector definition
                const vectorIndex = k.vector.findIndex(v => v !== 0);

                if (vectorIndex !== -1 && currentSong.vector && vectorIndex < currentSong.vector.length) {
                    // Get the value from the song's vector (0.0 - 1.0)
                    const songValue = currentSong.vector[vectorIndex];

                    // Map 0.0-1.0 to UI Range (0-100)
                    // We assume the song vector is normalized 0-1
                    // And we want to map it to the knob's min/max then to 0-100?
                    // No, the song vector IS the value.
                    // If knob min/max is -1 to 1, and song value is 0.8 (Energy),
                    // We want the knob to show 0.8.
                    // But wait, the knob UI is 0-100.
                    // And the knob's "defaultValue" in config is -1 to 1.

                    // Let's assume the song vector values are 0.0 to 1.0.
                    // And the UI expects 0-100.
                    // So simply * 100.

                    // Special case: Instrumentalness is inverted in config?
                    // "vector": [0.0, 0.0, 0.0, 0.0, -1.0] for Vocals
                    // If song has 0.0 instrumentalness (high vocals), we want High Vocals.
                    // If song has 1.0 instrumentalness (no vocals), we want Low Vocals.

                    let uiValue = songValue * 100;

                    // Handle inversion if the config vector is negative
                    if (k.vector[vectorIndex] < 0) {
                        uiValue = (1.0 - songValue) * 100;
                    }

                    newKnobs[k.id] = uiValue;
                }
            });

            setKnobs(newKnobs);
        }
    }, [currentSong, knobConfig]);

    // Trigger recommendation when a song is selected or knobs settle
    const fetchRecommendations = useCallback(async () => {
        if (!currentSong) return;
        try {
            // Normalize knobs based on config
            const normalizedKnobs: KnobState = {};
            Object.entries(knobs).forEach(([key, value]) => {
                const configDef = knobConfig?.knobs.find(k => k.id === key);
                if (configDef) {
                    // Map 0-100 back to min-max
                    const norm = ((value / 100) * (configDef.max - configDef.min)) + configDef.min;
                    normalizedKnobs[key.toLowerCase()] = norm;
                } else {
                    // Fallback if no config found (assume -1 to 1)
                    normalizedKnobs[key.toLowerCase()] = (value - 50) / 50;
                }
            });

            const data = await getRecommendations({
                current_song_id: currentSong.id,
                knobs: normalizedKnobs
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

    const [analysisStats, setAnalysisStats] = useState<{
        processingTime: string;
        fingerprintCount: number;
        vector?: number[];
    } | null>(null);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

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

                // Create URL for visualization
                const url = URL.createObjectURL(blob);
                setAudioUrl(url);

                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());

                try {
                    const result = await identifyAudio(blob);
                    setCurrentSong(result.song);

                    // Set stats from result
                    if (result.metadata) {
                        setAnalysisStats({
                            processingTime: result.metadata.processing_time,
                            fingerprintCount: result.metadata.fingerprint_count,
                            vector: result.vector
                        });
                    }

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
        knobConfig,
        analysisStats,
        audioUrl,
        updateKnob,
        addKnob,
        handleSearch,
        startListening,
        fetchRecommendations
    };
};

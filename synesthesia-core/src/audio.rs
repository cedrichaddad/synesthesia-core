use rustfft::{FftPlanner, num_complex::Complex};
use crate::window::hanning_window;

const WINDOW_SIZE: usize = 4096;
const HOP_SIZE: usize = 2048;

// BAND DEFINITIONS (Bin indices for 44.1kHz / 4096 size)
// Lows: 0-200Hz (bins 0-19)
// Mids: 200Hz-2kHz (bins 19-185)
// Highs: 2kHz+ (bins 185+)
const BAND_SPLITS: [usize; 4] = [0, 20, 200, WINDOW_SIZE / 2]; 

pub struct AudioFingerprinter {
    planner: FftPlanner<f32>,
}

impl AudioFingerprinter {
    pub fn new() -> Self {
        Self {
            planner: FftPlanner::new(),
        }
    }

    /// Packs two frequencies and a time delta into a single 64-bit integer.
    /// Layout: [Unused: 32] [F1: 12] [F2: 12] [Delta: 8]
    /// This fits perfectly in a register and compares instantly.
    #[inline(always)]
    fn pack_hash(f1: usize, f2: usize, dt: usize) -> u64 {
        ((f1 as u64) << 20) | ((f2 as u64) << 8) | (dt as u64)
    }

    pub fn fingerprint(&mut self, audio: &[f32]) -> Vec<(u64, usize)> {
        let fft = self.planner.plan_fft_forward(WINDOW_SIZE);
        let window = hanning_window(WINDOW_SIZE); // In prod, cache this!
        
        let num_windows = if audio.len() < WINDOW_SIZE { 
            0 
        } else {
            (audio.len() - WINDOW_SIZE) / HOP_SIZE 
        };
        
        // Pre-allocate to avoid reallocation spikes
        let mut spectrogram = Vec::with_capacity(num_windows);
        let mut fingerprints = Vec::new();

        // 1. COMPUTE SPECTROGRAM
        for i in 0..num_windows {
            let start = i * HOP_SIZE;
            let end = start + WINDOW_SIZE;
            
            let mut buffer: Vec<Complex<f32>> = audio[start..end]
                .iter()
                .zip(&window)
                .map(|(&sample, &win)| Complex::new(sample * win, 0.0))
                .collect();

            fft.process(&mut buffer);

            // Peak Picking with Bands
            let mut peaks = Vec::new();
            
            // Iterate over our 3 frequency bands (Low, Mid, High)
            for band in 0..3 {
                let min_bin = BAND_SPLITS[band];
                let max_bin = BAND_SPLITS[band + 1];
                
                let mut band_peaks = Vec::new();

                // Find Local Maxima in this band
                for bin in min_bin..max_bin {
                    if bin == 0 || bin >= buffer.len() - 1 { continue; }
                    
                    let mag = buffer[bin].norm();
                    let mag_prev = buffer[bin - 1].norm();
                    let mag_next = buffer[bin + 1].norm();

                    // Must be a local peak
                    if mag > mag_prev && mag > mag_next {
                        // Convert to dB: 20 * log10(mag)
                        let db = 20.0 * mag.log10();
                        
                        // Noise Floor Threshold (e.g., -40dB relative to max, or fixed)
                        if db > 10.0 { 
                            band_peaks.push((bin, db));
                        }
                    }
                }

                // Keep top K strongest peaks per band (prevents loud highs from hiding bass)
                band_peaks.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
                band_peaks.truncate(5); // Keep top 5 per band -> 15 peaks total per frame
                
                for (bin, _) in band_peaks {
                    peaks.push(bin);
                }
            }
            spectrogram.push(peaks);
        }

        // 2. GENERATE CONSTELLATION HASHES
        for (t1, peaks) in spectrogram.iter().enumerate() {
            for &f1 in peaks {
                // Target Zone: Look 1 to 10 frames ahead
                let look_ahead_max = (t1 + 10).min(spectrogram.len());
                
                for t2 in (t1 + 1)..look_ahead_max {
                    let dt = t2 - t1;
                    
                    for &f2 in &spectrogram[t2] {
                        // Generate the fingerprint
                        let hash = Self::pack_hash(f1, f2, dt);
                        
                        // Important: Return (Hash, Anchor_Time)
                        fingerprints.push((hash, t1));
                    }
                }
            }
        }

        fingerprints
    }
}
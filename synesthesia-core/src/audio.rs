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
    window: Vec<f32>,
    // Pre-allocated buffers for reuse
    fft_buffer: Vec<Complex<f32>>,
    peaks_buffer: Vec<usize>,
    band_peaks_buffer: Vec<(usize, f32)>,
}

impl AudioFingerprinter {
    pub fn new() -> Self {
        Self {
            planner: FftPlanner::new(),
            window: hanning_window(WINDOW_SIZE),
            fft_buffer: vec![Complex::zero(); WINDOW_SIZE],
            peaks_buffer: Vec::with_capacity(64),
            band_peaks_buffer: Vec::with_capacity(32),
        }
    }

    #[inline(always)]
    fn pack_hash(f1: usize, f2: usize, dt: usize) -> u64 {
        ((f1 as u64) << 20) | ((f2 as u64) << 8) | (dt as u64)
    }

    pub fn calculate_rms(audio: &[f32]) -> f32 {
        if audio.is_empty() { return 0.0; }
        let sum_squares: f32 = audio.iter().map(|&x| x * x).sum();
        (sum_squares / audio.len() as f32).sqrt()
    }

    pub fn calculate_spectral_flatness(&mut self, audio: &[f32]) -> f32 {
        if audio.len() < WINDOW_SIZE { return 0.0; }
        
        let fft = self.planner.plan_fft_forward(WINDOW_SIZE);
        
        // Prepare buffer
        for (i, (&sample, &win)) in audio.iter().zip(&self.window).enumerate().take(WINDOW_SIZE) {
            self.fft_buffer[i] = Complex::new(sample * win, 0.0);
        }
            
        fft.process(&mut self.fft_buffer);
        
        // Calculate power spectrum
        // Use a small epsilon to avoid log(0)
        let mut sum_val = 0.0;
        let mut log_sum = 0.0;
        
        for c in &self.fft_buffer {
            let mag = c.norm_sqr();
            sum_val += mag;
            log_sum += (mag + 1e-10).ln();
        }
        
        let arithmetic_mean = sum_val / WINDOW_SIZE as f32;
        let geometric_mean = (log_sum / WINDOW_SIZE as f32).exp();
        
        if arithmetic_mean == 0.0 { 0.0 } else { geometric_mean / arithmetic_mean }
    }

    pub fn analyze(&mut self, audio: &[f32]) -> (f32, f32) {
        let rms = Self::calculate_rms(audio);
        let flatness = self.calculate_spectral_flatness(audio);
        (rms, flatness)
    }

    pub fn fingerprint(&mut self, audio: &[f32]) -> Vec<(u64, usize)> {
        if audio.len() < WINDOW_SIZE { return Vec::new(); }

        let fft = self.planner.plan_fft_forward(WINDOW_SIZE);
        let num_windows = (audio.len() - WINDOW_SIZE) / HOP_SIZE;
        
        // We still need to store the full spectrogram history for the look-ahead
        // but we can optimize the inner loops.
        // For a true streaming implementation, this would be a ring buffer.
        // For this batch implementation, we'll keep the vector of vectors but optimize the inner allocation.
        let mut spectrogram = Vec::with_capacity(num_windows);
        let mut fingerprints = Vec::new();

        // 1. COMPUTE SPECTROGRAM
        for i in 0..num_windows {
            let start = i * HOP_SIZE;
            
            // Fill buffer
            for (j, (&sample, &win)) in audio[start..].iter().zip(&self.window).enumerate().take(WINDOW_SIZE) {
                self.fft_buffer[j] = Complex::new(sample * win, 0.0);
            }

            fft.process(&mut self.fft_buffer);

            // Reuse peak buffer for this frame
            self.peaks_buffer.clear();
            
            for band in 0..3 {
                let min_bin = BAND_SPLITS[band];
                let max_bin = BAND_SPLITS[band + 1];
                
                self.band_peaks_buffer.clear();

                for bin in min_bin..max_bin {
                    if bin == 0 || bin >= WINDOW_SIZE - 1 { continue; }
                    
                    let mag = self.fft_buffer[bin].norm();
                    let mag_prev = self.fft_buffer[bin - 1].norm();
                    let mag_next = self.fft_buffer[bin + 1].norm();

                    if mag > mag_prev && mag > mag_next {
                        let db = 20.0 * mag.log10();
                        if db > 10.0 { 
                            self.band_peaks_buffer.push((bin, db));
                        }
                    }
                }

                // Sort and take top 5
                self.band_peaks_buffer.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
                
                for (bin, _) in self.band_peaks_buffer.iter().take(5) {
                    self.peaks_buffer.push(*bin);
                }
            }
            // We have to clone here to persist the frame in the spectrogram history
            spectrogram.push(self.peaks_buffer.clone());
        }

        // 2. GENERATE HASHES
        for (t1, peaks) in spectrogram.iter().enumerate() {
            for &f1 in peaks {
                let look_ahead_max = (t1 + 10).min(spectrogram.len());
                
                for t2 in (t1 + 1)..look_ahead_max {
                    let dt = t2 - t1;
                    for &f2 in &spectrogram[t2] {
                        let hash = Self::pack_hash(f1, f2, dt);
                        fingerprints.push((hash, t1));
                    }
                }
            }
        }

        fingerprints
    }
}
use pyo3::prelude::*;
use crate::audio::AudioFingerprinter;

mod audio;
mod window;

/// A robust, memory-efficient fingerprint structure exposed to Python.
/// Uses u64 for the hash to avoid string allocation overhead.
#[pyclass]
pub struct Fingerprint {
    #[pyo3(get)]
    pub hash: u64,
    #[pyo3(get)]
    pub offset: u32, // The time "anchor" for alignment verification
}

use numpy::PyReadonlyArray1;

#[pyfunction]
fn audio_fingerprint(_py: Python, audio_buffer: PyReadonlyArray1<f32>) -> PyResult<Vec<Fingerprint>> {
    let mut fingerprinter = AudioFingerprinter::new();
    
    // Zero-copy access to the numpy array
    let audio_slice = audio_buffer.as_slice()?;
    
    // The Rust engine returns raw tuples (hash, offset)
    let raw_data = fingerprinter.fingerprint(audio_slice);
    
    // Map to the PyClass struct for Python consumption
    let result = raw_data
        .into_iter()
        .map(|(h, t)| Fingerprint { hash: h, offset: t as u32 })
        .collect();

    Ok(result)
}

#[pyfunction]
fn audio_analyze(_py: Python, audio_buffer: PyReadonlyArray1<f32>) -> PyResult<(f32, f32)> {
    let mut fingerprinter = AudioFingerprinter::new();
    
    // Zero-copy access to the numpy array
    let audio_slice = audio_buffer.as_slice()?;
    
    // Analyze
    let (rms, flatness) = fingerprinter.analyze(audio_slice);
    
    Ok((rms, flatness))
}

#[pymodule]
fn core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Fingerprint>()?;
    m.add_function(wrap_pyfunction!(audio_fingerprint, m)?)?;
    m.add_function(wrap_pyfunction!(audio_analyze, m)?)?;
    Ok(())
}
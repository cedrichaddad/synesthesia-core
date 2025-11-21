# Synesthesia Core

Real-time latent space audio navigation system.

## Prerequisites

- **Rust**: Latest stable (`rustup`).
- **Python**: 3.11 (Strict requirement).
- **FFmpeg**: Required for audio processing.
- **Docker**: For Qdrant and production build.

## Environment Variables

Create a `.env` file in `synesthesia-core/`:

```bash
SPOTIPY_CLIENT_ID="your_spotify_client_id"
SPOTIPY_CLIENT_SECRET="your_spotify_client_secret"
SPOTIPY_REDIRECT_URI="http://127.0.0.1:3000/callback"
```

## Local Development

1.  **Install Dependencies**:
    ```bash
    # Install Python dependencies & build Rust extension
    maturin develop
    ```

2.  **Start Qdrant**:
    ```bash
    docker-compose up -d
    ```

3.  **Ingest Data**:
    ```bash
    python scripts/ingest.py
    ```

4.  **Run API**:
    ```bash
    uvicorn synesthesia.api:app --reload
    ```

5.  **Run Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

    **Important**: Access the application at `http://127.0.0.1:3000` (NOT `localhost:3000`) to ensure Spotify OAuth redirects work correctly.

## Production Build (Docker)

1.  **Build Image**:
    ```bash
    docker build -t synesthesia-core .
    ```

2.  **Run Container**:
    ```bash
    docker run -p 8000:8000 --env-file .env synesthesia-core
    ```

## Testing

Run unit tests with mocks (no heavy models loaded):

```bash
pytest tests/
```

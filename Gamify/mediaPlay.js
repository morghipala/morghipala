class AudioPlayer {
    constructor(url) {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.buffer = null;
        this.source = null;
        this.metadata = null;
        this.startTime = 0;
        this.pausedAt = 0;
        this._isLoading = false;
        this._isPlaying = false;
        this._isPaused = false;
        this._loopEnabled = false;
        this.onEndCallback = null;

        if (url) {
            return this.initialize(url);
        }
    }

    async initialize(url) {
        this._isLoading = true;

        try {
            // Carica il metadata JSON
            const jsonUrl = url.replace(/\.[^/.]+$/, '.json');
            const [metadataResponse, audioResponse] = await Promise.all([
                fetch(jsonUrl),
                fetch(url)
            ]);

            this.metadata = await metadataResponse.json();
            const arrayBuffer = await audioResponse.arrayBuffer();
            this.buffer = await this.audioContext.decodeAudioData(arrayBuffer);

            this._isLoading = false;
            return this;
        } catch (error) {
            console.error('Error loading media:', error);
            this._isLoading = false;
            throw error;
        }
    }

    play() {
        if (!this.buffer || this._isPlaying) return;

        const offset = this._isPaused ? this.pausedAt : 0;
        this.stop();

        this.source = this.audioContext.createBufferSource();
        this.source.buffer = this.buffer;

        if (this._loopEnabled) {
            this.source.loop = true;
            this.source.loopStart = this.metadata.beginning;
            this.source.loopEnd = this.metadata.beginning + this.metadata.loop;
        }

        this.source.connect(this.audioContext.destination);
        this.startTime = this.audioContext.currentTime - offset;
        
        if (!this._isPaused) {
            this.source.start(0);
        } else {
            this.source.start(0, offset);
        }

        this._isPlaying = true;
        this._isPaused = false;

        this.source.onended = () => {
            if (!this._loopEnabled) {
                this._isPlaying = false;
                if (this.onEndCallback) this.onEndCallback();
            }
        };
    }

    pause() {
        if (!this.source || !this._isPlaying) return;

        const elapsed = this.audioContext.currentTime - this.startTime;
        this.stop();
        this.pausedAt = elapsed;
        this._isPaused = true;
    }

    stop() {
        if (this.source) {
            this.source.stop();
            this.source.disconnect();
        }
        this.source = null;
        this._isPlaying = false;
        this.pausedAt = 0;
    }

    loop(enabled) {
        this._loopEnabled = enabled;
        localStorage.setItem("loop", enabled)
    }

    getCurrentTime() {
        if (!this._isPlaying) return this.pausedAt;
        return this.audioContext.currentTime - this.startTime;
    }

    isPlaying() {
        return this._isPlaying;
    }

    isPaused() {
        return this._isPaused;
    }

    isLoading() {
        return this._isLoading;
    }

    loopState() {
        return this._loopEnabled;
    }
}
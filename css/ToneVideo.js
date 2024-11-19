// ToneVideo.js

const ToneVideo = (() => {
    const settings = {
        controls: true,
        autoplay: true,
        loop: false
    };

    let openingStart = null;
    let openingEnd = null;
    let creditsStart = null;
    let creditsTimer;
    let creditsCountdown;
    let timerActive = false;
    let hasEnteredCredits = false;

    const formatTime = (seconds) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const formattedSeconds = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(formattedSeconds).padStart(2, '0')}`;
        } else {
            return `${String(minutes).padStart(2, '0')}:${String(formattedSeconds).padStart(2, '0')}`;
        }
    };

    const createCustomControls = (videoElement) => {
        const controlsWrapper = document.createElement('div');
        controlsWrapper.classList.add('tone-video-controls');

        const playButton = document.createElement('button');
        playButton.innerHTML = '<i class="material-icons">play_arrow</i>';
        playButton.classList.add('play-btn');

        const progressBar = document.createElement('input');
        progressBar.type = 'range';
        progressBar.classList.add('progress-bar');
        progressBar.value = 0;
        progressBar.min = 0;
        progressBar.max = videoElement.duration || 0;

        const before = document.createElement('div');
        before.classList.add('before');
        before.innerHTML = '00:00';

        const after = document.createElement('div');
        after.classList.add('after');
        after.innerHTML = '00:00';

        const muteButton = document.createElement('button');
        muteButton.innerHTML = '<i class="material-icons">volume_off</i>';
        muteButton.classList.add('mute-btn');

        const fullscreenButton = document.createElement('button');
        fullscreenButton.classList.add('fullscreen-btn');
        fullscreenButton.innerHTML = '<i class="material-icons">fullscreen</i>';
        fullscreenButton.addEventListener('click', function (e) {
            toggleFullscreen(findNearestVideo(e.target));
          });

        const skipForwardButton = document.createElement('button');
        skipForwardButton.innerHTML = '<i class="material-icons">forward_10</i>';
        skipForwardButton.classList.add('skip-forward-btn');

        const skipBackwardButton = document.createElement('button');
        skipBackwardButton.innerHTML = '<i class="material-icons">replay_10</i>';
        skipBackwardButton.classList.add('skip-backward-btn');

        const controlsContainer = document.createElement('div');
        controlsContainer.classList.add('controls-container');


        // Aggiungi il pulsante per selezionare la lingua dei sottotitoli
        const subtitleButton = document.createElement('button');
        subtitleButton.innerHTML = '<i class="material-icons">subtitles</i>';
        subtitleButton.classList.add('subtitle-btn');
        subtitleButton.addEventListener('click', () => openSubtitlePopup(videoElement));

        controlsWrapper.appendChild(before);
        controlsWrapper.appendChild(progressBar);
        controlsWrapper.appendChild(after);
        controlsWrapper.appendChild(subtitleButton);
        controlsWrapper.appendChild(fullscreenButton);
        controlsContainer.appendChild(controlsWrapper);
        controlsContainer.appendChild(playButton);
        controlsContainer.appendChild(skipBackwardButton);
        controlsContainer.appendChild(skipForwardButton);

        const videoContainer = document.createElement('div');
        videoContainer.classList.add('tone-video-container');
        videoContainer.classList.add('ToneHidden');
        videoContainer.classList.add('ToneVideo');

        const videoParent = videoElement.parentNode;
        videoParent.removeChild(videoElement);
        videoContainer.appendChild(videoElement);
        videoContainer.appendChild(controlsContainer);

        videoParent.insertBefore(videoContainer, videoParent.querySelector('.episode-details') || null);

        let inactivityTimer;
        const inactivityDelay = 3000;

        const resetInactivityTimer = () => {
            clearTimeout(inactivityTimer);
            videoContainer.classList.remove('ToneHidden');
            inactivityTimer = setTimeout(() => {
                videoContainer.classList.add('ToneHidden');
            }, inactivityDelay);
        };

        videoContainer.addEventListener('mousemove', resetInactivityTimer);
        videoContainer.addEventListener('click', resetInactivityTimer);
        videoContainer.addEventListener('mouseleave', () => {
            videoContainer.classList.add('ToneHidden');
        });

        playButton.addEventListener('click', () => togglePlay(videoElement, playButton));
        progressBar.addEventListener('input', (e) => updateProgress(videoElement, e.target.value));
        muteButton.addEventListener('click', () => toggleMute(videoElement, muteButton));
        skipForwardButton.addEventListener('click', () => skipVideo(videoElement, 10));
        skipBackwardButton.addEventListener('click', () => skipVideo(videoElement, -10));

        const updateTimeVariables = (videoElement) => {
            const currentTime = videoElement.currentTime;
            const duration = videoElement.duration || 0;
            const container = findNearestVideo(videoElement);
            const before = container.querySelector('.before');
            const after = container.querySelector('.after');
            const progressBar = container.querySelector('.progress-bar');
            const formattedCurrentTime = formatTime(currentTime);
            const formattedDuration = duration ? formatTime(duration) : '00:00';

            
            progressBar.max = videoElement.duration;
            progressBar.value = videoElement.currentTime;

            before.innerHTML = formattedCurrentTime;
            after.innerHTML = formattedDuration;
        };

        videoElement.addEventListener('loadedmetadata', function (e) {
            updateTimeVariables(e.target);
        });

        videoElement.ontimeupdate = (event) => {
            updateTimeVariables(videoElement);
            checkForSegments(videoElement.currentTime);
        };

        updateTimeVariables(videoElement);

        function updateButton() {
            playButton.innerHTML = videoElement.paused ? '<i class="material-icons">play_arrow</i>' : '<i class="material-icons">pause</i>';
        }

        videoElement.addEventListener('play', updateButton);
        videoElement.addEventListener('pause', updateButton);
    };

    const toggleFullscreen = (videoElement) => {
        videoElement.classList.toggle('fullscreen');
        if (videoElement.classList.contains('fullscreen')) {
            videoElement.requestFullscreen().catch(err => {
                console.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
            });
        } else {
            document.exitFullscreen().catch(err => {
                console.error(`Error attempting to exit full-screen mode: ${err.message} (${err.name})`);
            });
        }
    };

    const togglePlay = (video, button) => {
        if (video.paused) {
            video.play();
            clearCreditsTimer();
        } else {
            video.pause();
            clearCreditsTimer();
        }
    };

    const updateProgress = (video, value) => {
        video.currentTime = value;
    };

    const skipVideo = (video, seconds) => {
        if (seconds > 0) {
            video.currentTime += 10;
        } else {
            video.currentTime -= 10;
        }
        clearCreditsTimer()
    };

    const toggleMute = (video, button) => {
        video.muted = !video.muted;
        button.innerHTML = video.muted ? '<i class="material-icons">volume_mute</i>' : '<i class="material-icons">volume_up</i>';
    };

    const init = (elements) => {
        const videoElements = Array.isArray(elements) ? elements : [elements];

        videoElements.forEach((element) => {
            if (element.tagName.toLowerCase() === 'video') {
                element.controls = false;
                createCustomControls(element);
                element.autoplay = settings.autoplay;
                element.play();
            } else {
                console.warn('Elemento non valido. Deve essere un elemento <video>.');
            }
        });
    };

    const setOpening = (videoElement, start, end) => {
        openingStart = convertToSeconds(start);
        openingEnd = convertToSeconds(end);
        checkForSegments(videoElement.currentTime);
    };

    const setCredits = (videoElement, start) => {
        creditsStart = convertToSeconds(start);
        checkForSegments(videoElement.currentTime);
    };

    const checkForSegments = (currentTime) => {
        const videoElement = document.querySelector('.tone-video-container video');

        const openingEndValid = openingEnd !== null && openingEnd !== 0;
        const creditsStartValid = creditsStart !== null && creditsStart !== 0;

        if (openingStart !== null && currentTime >= openingStart && (openingEndValid ? currentTime < openingEnd : true)) {
            if (openingEndValid && openingEnd !== 0) {
                showSkipButton();
            }
            clearCreditsTimer();
            hasEnteredCredits = false;
        } else {
            hideSkipBtn();
        }

        if (creditsStartValid && currentTime >= creditsStart) {
            if (!hasEnteredCredits) {
                showCreditsButton();
                hasEnteredCredits = true;
            }
        } else {
            clearCreditsTimer();
            hideButtons();
            hasEnteredCredits = false;
        }

        if (videoElement.paused) {
            clearCreditsTimer();
        }
    };

    const showSkipButton = () => {
        const videoElement = document.querySelector('.tone-video-container video');
        const controlsContainer = videoElement.parentNode.querySelector('.controls-container');

        if (!controlsContainer.querySelector('.skip-btn')) {
            const skipButton = document.createElement('button');
            skipButton.classList.add('skip-btn');
            skipButton.innerHTML = 'Skip Opening';
            skipButton.addEventListener('click', skipOpening);
            controlsContainer.appendChild(skipButton);
        }
    };

    const showCreditsButton = () => {
        const videoElement = document.querySelector('.tone-video-container video');
        const controlsContainer = videoElement.parentNode.querySelector('.controls-container');

        if (!controlsContainer.querySelector('.credits-btn')) {
            const creditsButton = document.createElement('button');
            creditsButton.classList.add('credits-btn');

            creditsButton.addEventListener('click', () => {
                goToNextEpisode();
                clearCreditsTimer();
                timerActive = false;
            });

            const cancelButton = document.createElement('button');
            cancelButton.innerHTML = '×';
            cancelButton.classList.add('cancel-btn');
            cancelButton.addEventListener('click', clearCreditsTimer);
            creditsButton.appendChild(cancelButton);

            let countdownTime = 10;
            creditsButton.innerHTML = `Next episode in ${countdownTime}s`;

            creditsCountdown = setInterval(() => {
                countdownTime--;
                creditsButton.innerHTML = `Next episode in ${countdownTime}s`;
                if (countdownTime <= 0) {
                    goToNextEpisode();
                    clearCreditsTimer();
                    timerActive = false;
                }
            }, 1000);

            controlsContainer.appendChild(creditsButton);
        }
    };

    const clearCreditsTimer = () => {
        clearInterval(creditsCountdown);
        creditsCountdown = null;
        timerActive = false;
        try {
            const creditsButton = document.querySelector('.credits-btn');
            creditsButton.innerHTML = 'Next episode';
        } catch (error) { }
    };

    const hideCreditsButton = () => {
        const creditsButton = document.querySelector('.credits-btn');
        if (creditsButton) {
            creditsButton.remove();
        }
    };

    const skipOpening = () => {
        const videoElement = document.querySelector('.tone-video-container video');
        videoElement.currentTime = openingEnd;
        videoElement.play();
        hideButtons();
    };

    const goToNextEpisode = () => {
        clearCreditsTimer();
        const nextButton = document.getElementById('Next');
        if (nextButton) {
            nextButton.click();
        } else {
            console.warn('Pulsante "Next" non trovato.');
        }
        hideButtons();
    };

    const hideButtons = () => {
        hideCreditsButton();
    };

    const hideSkipBtn = () => {
        const skipButton = document.querySelector('.skip-btn');
        if (skipButton) skipButton.remove();
    };

    const convertToSeconds = (time) => {
        const parts = time.split(':');
        return parts.length === 2 ? parseInt(parts[0]) * 60 + parseInt(parts[1]) : 0;
    };

    const setEpisodeDetails = (videoElement, title, season = null, episode = null, episodeName = null) => {
        const existingDetails = videoElement.parentNode.querySelector('.episode-details');
        if (!existingDetails) {
            const detailsDiv = document.createElement('div');
            detailsDiv.classList.add('episode-details');

            const titleElement = document.createElement('strong');
            titleElement.textContent = title + " ";
            detailsDiv.appendChild(titleElement);

            if (season !== null && episode !== null && episodeName !== null) {
                detailsDiv.innerHTML += ` S${season}-E${episode} ${episodeName}`;
            }

            videoElement.parentNode.insertBefore(detailsDiv, videoElement);
        } else {
            const titleElement = existingDetails.querySelector('strong');
            titleElement.textContent = title + " ";

            if (season !== null && episode !== null && episodeName !== null) {
                existingDetails.innerHTML = `S${season}-E${episode} ${episodeName}`;
                existingDetails.prepend(titleElement);
            }
        }
    };

    const addButton = (videoElement, onClickFunction, id) => {
        const controlsWrapper = videoElement.parentNode.querySelector('.tone-video-controls');
        if (!controlsWrapper) {
            console.warn('Controlli non trovati. Assicurati che i controlli siano stati creati.');
            return;
        }

        const button = document.createElement('button');
        button.classList.add('custom-btn');
        button.id = id;

        // Se il nome del pulsante è "Next", usa l'icona "skip_next" di Material Design
        if (id === "Next") {
            button.innerHTML = '<i class="material-icons">skip_next</i>';
        } else {
            button.textContent = id;
        }

        button.setAttribute('onclick', onClickFunction);

        const fullscreenButton = controlsWrapper.querySelector('.fullscreen-btn');
        if (fullscreenButton) {
            controlsWrapper.insertBefore(button, fullscreenButton);
        } else {
            controlsWrapper.appendChild(button); // Fallback nel caso in cui il pulsante fullscreen non esista
        }
    };


    const removeButton = (videoElement, id) => {
        const button = videoElement.parentNode.querySelector(`#${id}`);
        if (button) {
            button.remove();
        } else {
            console.warn(`Pulsante con ID "${id}" non trovato.`);
        }
    };

    document.addEventListener('keydown', (event) => {
        const videoElement = document.querySelector('.tone-video-container video');
        if (!videoElement) return;

        switch (event.code) {
            case 'Space':
                event.preventDefault();
                togglePlay(videoElement, document.querySelector('.pause-btn'));
                break;
            case 'ArrowRight':
                event.preventDefault();
                skipVideo(videoElement, 10);
                break;
            case 'ArrowLeft':
                event.preventDefault();
                skipVideo(videoElement, -10);
                break;
            default:
                break;
        }
    });

    const openSubtitlePopup = (videoElement) => {
        if (findNearestVideo(videoElement).querySelector('.subtitle-popup')) {
            findNearestVideo(videoElement).querySelector('.subtitle-popup').remove();
            return;
        }

        const subtitlePopup = document.createElement('div');
        subtitlePopup.classList.add('subtitle-popup');

        const subtitleTracks = videoElement.textTracks;
        if (subtitleTracks.length === 0) {
            subtitlePopup.innerHTML = 'No subtitles available';
        } else {
            // Aggiungi lo switch per attivare/disattivare i sottotitoli
            const subtitleSwitchContainer = document.createElement('div');
            subtitleSwitchContainer.classList.add('subtitle-switch-container');

            const subtitleSwitchLabel = document.createElement('label');
            subtitleSwitchLabel.textContent = 'Subtitles:';

            const subtitleSwitch = document.createElement('input');
            subtitleSwitch.type = 'checkbox';
            subtitleSwitch.checked = Array.from(subtitleTracks).some(track => track.mode === 'showing');

            subtitleSwitch.addEventListener('change', (event) => {
                const isChecked = event.target.checked;
                setSubtitleLanguage(videoElement, isChecked ? select.value : '');
            });

            subtitleSwitchContainer.appendChild(subtitleSwitchLabel);
            subtitleSwitchContainer.appendChild(subtitleSwitch);
            subtitlePopup.appendChild(subtitleSwitchContainer);

            // Crea il selettore dei sottotitoli
            const select = document.createElement('select');
            if (!subtitleSwitch.checked) {
                select.style.display = 'none';
            }
            select.classList.add('subtitle-select');
            select.id = 'subtitle-select';

            Array.from(subtitleTracks).forEach(track => {

                const option = document.createElement('option');
                option.value = track.language;
                option.textContent = track.label;
                if (track.language === localStorage.getItem('lang')) {
                    option.selected = true;
                }
                select.appendChild(option);
            });

            select.addEventListener('change', (event) => {
                setSubtitleLanguage(videoElement, event.target.value);
            });

            subtitleSwitch.addEventListener('change', (event) => {
                // Nascondi il selettore se i sottotitoli sono disattivati
                select.style.display = subtitleSwitch.checked ? 'block' : 'none';
            });

            subtitlePopup.appendChild(select);
        }

        // Aggiungi il pulsante di chiusura
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '×';
        closeButton.classList.add('close-btn');
        closeButton.addEventListener('click', () => subtitlePopup.remove());

        subtitlePopup.appendChild(closeButton);

        // Aggiungi il popup al corpo della pagina
        findNearestVideo(videoElement).appendChild(subtitlePopup);

        setTimeout(() => {

            // Aggiungi un listener per chiudere il popup quando si clicca fuori di esso
            document.addEventListener('click', (event) => {
                // Controlla se il clic è fuori dal popup
                if (!subtitlePopup.contains(event.target) && !event.target.closest('.subtitle-popup')) {
                    event.preventDefault()
                    subtitlePopup.remove();  // Rimuove il popup
                }
            });
        }, 2);
    };

    const setSubtitleLanguage = (videoElement, language) => {
        if (language !== '' && language !== 'disabled') {
            localStorage.setItem('lang', language);
            localStorage.setItem('subt', 'true');
        } else if (language !== 'disabled') {
            localStorage.setItem('subt', 'false');
        }

        const subtitleTracks = videoElement.textTracks;
        for (let i = 0; i < subtitleTracks.length; i++) {
            subtitleTracks[i].mode = subtitleTracks[i].language === language ? 'showing' : 'disabled';
        }
    };

    const showSubtitles = (videoElement) => {
        try {
            const subtitleControl = document.querySelector('.subtitle-btn');
            subtitleControl.setAttribute('style', 'display: block');
            ToneVideo.setSubtitleLanguage(videoElement, 'disabled');
        } catch (error) {
            console.log(error);
        }
    }

    const hideSubtitles = (videoElement) => {
        try {
            const subtitleControl = document.querySelector('.subtitle-btn');
            subtitleControl.setAttribute('style', 'display: none');
            ToneVideo.setSubtitleLanguage(videoElement, 'disabled');
        } catch (error) {
            console.log(error);
        }
    }

    function findNearestVideo(element) {
        if (!(element instanceof HTMLElement)) {
            throw new Error("Il parametro deve essere un elemento HTML.");
        }
    
        // Controlla se l'elemento stesso è un <video>
        if (element.tagName.toLowerCase() === ".tone-video-container") {
            return element;
        }
    
        // Cerca l'antenato più vicino con il tag <video>
        const closestVideo = element.closest(".tone-video-container");
        if (closestVideo) {
            return closestVideo;
        }
    
        // Cerca nei fratelli dell'elemento
        let sibling = element.previousElementSibling;
        while (sibling) {
            if (sibling.tagName.toLowerCase() === ".tone-video-container") {
                return sibling;
            }
            sibling = sibling.previousElementSibling;
        }
    
        sibling = element.nextElementSibling;
        while (sibling) {
            if (sibling.tagName.toLowerCase() === ".tone-video-container") {
                return sibling;
            }
            sibling = sibling.nextElementSibling;
        }
    
        // Cerca tra i discendenti dell'elemento
        const descendantVideo = element.querySelector(".tone-video-container");
        if (descendantVideo) {
            return descendantVideo;
        }
    
        // Se nessun video è trovato, restituisci null
        return null;
    }

    const api = { init, setEpisodeDetails, addButton, removeButton, setOpening, setCredits, setSubtitleLanguage, showSubtitles, hideSubtitles, formatTime };
    return api;


})();

window.ToneVideo = ToneVideo;

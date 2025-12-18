// Main JavaScript file voor alle pagina's
// Transport HMI functionaliteit

// Snelheid in stappen 0..10 (0 = 0.0, 10 = 1.0)
let currentSpeedLevel = 6;  // default 6 → 0.6 PWM

// iets met knoppen uitzetten
let UI_LOCK = {
  locked: false,
  activeBtn: null,
  disabled: new Map(), // btn -> previousDisabled
};

// Wacht tot de DOM geladen is
document.addEventListener('DOMContentLoaded', function() {
    console.log('Main.js geladen');
    
    // Initialiseer dropdown functionaliteit
    initializeDropdowns();

    // Initialiseer automatische modus knoppen (start/stop)
    initializeAutomaticControls();

    // initialiseer inductie sensor
    initializeSensorIndicators(); 

    // Initialiseer x-as motor
    initializeManualControls();

    // Initialiseer de speed control van de x-as
    initializeSpeedControl();

    // Initialiseer encoder en potmeter
    initializeManualSensors();

    // Initialiseer homing
    initializeHomingButton();
});


// Dropdown functionaliteit
function initializeDropdowns() {
    // Zoek alle dropdown buttons
    const dropdownButtons = document.querySelectorAll('[id$="-dropdown-btn"]');
    
    dropdownButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Vind het bijbehorende dropdown menu
            const buttonId = this.id;
            const menuId = buttonId.replace('-btn', '-menu');
            const dropdownMenu = document.getElementById(menuId);
            
            if (dropdownMenu) {
                toggleDropdown(dropdownMenu);
            }
        });
    });
    
    // Sluit dropdown als er buiten geklikt wordt
    document.addEventListener('click', function(e) {
        const dropdowns = document.querySelectorAll('[id$="-dropdown-menu"]');
        dropdowns.forEach(dropdown => {
            if (!dropdown.contains(e.target) && !e.target.closest('[id$="-dropdown-btn"]')) {
                closeDropdown(dropdown);
            }
        });
    });
}

// Toggle dropdown menu open/dicht
function toggleDropdown(dropdownMenu) {
    const isHidden = dropdownMenu.classList.contains('hidden');
    
    if (isHidden) {
        openDropdown(dropdownMenu);
    } else {
        closeDropdown(dropdownMenu);
    }
}

// Open dropdown menu
function openDropdown(dropdownMenu) {
    dropdownMenu.classList.remove('hidden');
    dropdownMenu.classList.add('flex');
    
    // Kleine delay voor smooth animatie
    setTimeout(() => {
        dropdownMenu.classList.remove('scale-0', 'opacity-0');
        dropdownMenu.classList.add('scale-100', 'opacity-100');
    }, 10);
}

// Sluit dropdown menu
function closeDropdown(dropdownMenu) {
    dropdownMenu.classList.remove('scale-100', 'opacity-100');
    dropdownMenu.classList.add('scale-0', 'opacity-0');
    
    // Wacht op animatie voordat je het verbergt
    setTimeout(() => {
        dropdownMenu.classList.remove('flex');
        dropdownMenu.classList.add('hidden');
    }, 300);
}

// Selecteer een optie uit de dropdown
function selectOption(optionElement) {
    const dropdownMenu = optionElement.closest('[id$="-dropdown-menu"]');
    const menuId = dropdownMenu.id;
    const buttonId = menuId.replace('-menu', '-btn');
    const button = document.getElementById(buttonId);
    
    // Update button text met geselecteerde optie
    if (button) {
        const buttonText = button.childNodes[0];
        if (buttonText) {
            buttonText.textContent = optionElement.textContent.trim();
        }
    }
    
    // Sluit dropdown
    closeDropdown(dropdownMenu);
    
    // Trigger custom event voor andere scripts
    const selectEvent = new CustomEvent('dropdownSelect', {
        detail: {
            selectedValue: optionElement.textContent.trim(),
            selectedElement: optionElement,
            dropdownId: menuId
        }
    });
    document.dispatchEvent(selectEvent);
    
    console.log('Geselecteerde optie:', optionElement.textContent.trim());
}

// Hulpfunctie om items aan dropdown toe te voegen
function addDropdownOption(dropdownMenuId, text, value = null) {
    const dropdownMenu = document.getElementById(dropdownMenuId);
    if (!dropdownMenu) return;
    
    const option = document.createElement('div');
    option.className = 'p-2 flex items-center justify-center hover:bg-background-hover hover:rounded-md cursor-pointer dark:hover:bg-background-hoverDark';
    option.setAttribute('data-menu', 'graph-menu');
    option.setAttribute('onclick', 'selectOption(this)');
    option.textContent = text;
    
    if (value) {
        option.setAttribute('data-value', value);
    }
    
    dropdownMenu.appendChild(option);
}

// Hulpfunctie om dropdown leeg te maken
function clearDropdownOptions(dropdownMenuId) {
    const dropdownMenu = document.getElementById(dropdownMenuId);
    if (!dropdownMenu) return;
    
    dropdownMenu.innerHTML = '';
}

function initializeAutomaticControls() {
    // Zoek de knoppen alleen op pagina's waar ze bestaan
    const startBtn = document.getElementById('btn-start');
    const stopBtn  = document.getElementById('btn-stop');
    const messageBox = document.getElementById('message-box');

    // Als deze pagina geen start/stop knoppen heeft, niks doen
    if (!startBtn || !stopBtn) {
        return;
    }

    console.log('Automatic controls gevonden, event listeners worden gekoppeld');

    // Klik-handler voor Start
    startBtn.addEventListener('click', function() {
        sendAutomaticCommand('start', messageBox);
    });

    // Klik-handler voor Stop
    stopBtn.addEventListener('click', function() {
        sendAutomaticCommand('stop', messageBox);
    });
}

// Stuurt een commando naar de backend om de LED/GPIO aan te sturen
async function sendAutomaticCommand(action, messageBox) {
    try {
        const response = await fetch('/api/automatic/led', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ action: action })  // { "action": "start" } of "stop"
        });

        const data = await response.json();
        console.log('Server response:', data);

        if (messageBox) {
            if (data.success) {
                messageBox.textContent = action === 'start'
                    ? 'Transport line started (LED aan).'
                    : 'Transport line stopped (LED uit).';
            } else {
                messageBox.textContent = 'Error: ' + (data.error || 'Onbekende fout');
            }
        }
    } catch (err) {
        console.error('Fout bij versturen commando:', err);
        if (messageBox) {
            messageBox.textContent = 'Kon geen verbinding maken met de server.';
        }
    }
}

// =====================
// Sensor status indicators (manual page)
// =====================

function initializeSensorIndicators() {
    const sensorDot = document.getElementById('sensor-1-dot');

    // Als deze pagina geen sensor-bolletje heeft, doe niks
    if (!sensorDot) {
        return;
    }

    console.log('Sensor indicator gevonden, start polling...');

    // Elke 250 ms status opvragen
    setInterval(() => {
        updateSensorIndicator(sensorDot);
    }, 250);
}

async function updateSensorIndicator(sensorDot) {
    try {
        const response = await fetch('/api/sensors/1');
        if (!response.ok) {
            throw new Error('HTTP ' + response.status);
        }

        const data = await response.json();
        const active = !!data.active; // true/false

        // Tailwind classes togglen
        if (active) {
            sensorDot.classList.remove('bg-gray-300');
            sensorDot.classList.add('bg-green-400');
        } else {
            sensorDot.classList.remove('bg-green-400');
            sensorDot.classList.add('bg-gray-300');
        }
    } catch (err) {
        console.error('Fout bij lezen sensor status:', err);
        // hier zou je eventueel het bolletje op een error-kleur kunnen zetten
    }
}

// =====================
// X-as motor (manual page)
// =====================

function initializeManualControls() {
    const forwardBtn  = document.getElementById('btn-forward');
    const backwardBtn = document.getElementById('btn-backward');

    if (!forwardBtn && !backwardBtn) {
        return;
    }

    console.log('Manual controls gevonden – motor events gekoppeld');

    // helper om huidige snelheid als 0.0–1.0 te krijgen
    const getCurrentSpeed = () => currentSpeedLevel / 10.0;

    // ===== FORWARD =====
    const startForward = () => {
        sendManualMotorCommand('forward', 'start', getCurrentSpeed());
    };

    const stopForward = () => {
        sendManualMotorCommand('forward', 'stop', 0.0);
    };

    if (forwardBtn) {
        forwardBtn.addEventListener('mousedown', startForward);
        forwardBtn.addEventListener('mouseup', stopForward);
        forwardBtn.addEventListener('mouseleave', stopForward);

        forwardBtn.addEventListener('touchstart', e => {
            e.preventDefault();
            startForward();
        });
        forwardBtn.addEventListener('touchend', e => {
            e.preventDefault();
            stopForward();
        });
    }

    // ===== BACKWARD =====
    const startBackward = () => {
        sendManualMotorCommand('backward', 'start', getCurrentSpeed());
    };

    const stopBackward = () => {
        sendManualMotorCommand('backward', 'stop', 0.0);
    };

    if (backwardBtn) {
        backwardBtn.addEventListener('mousedown', startBackward);
        backwardBtn.addEventListener('mouseup', stopBackward);
        backwardBtn.addEventListener('mouseleave', stopBackward);

        backwardBtn.addEventListener('touchstart', e => {
            e.preventDefault();
            startBackward();
        });
        backwardBtn.addEventListener('touchend', e => {
            e.preventDefault();
            stopBackward();
        });
    }
}

async function sendManualMotorCommand(direction, action, speed) {
    try {
        const response = await fetch('/api/manual/motor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                direction: direction,  // "forward" of later "backward"
                action: action,        // "start" of "stop"
                speed: speed           // 0.0 t/m 1.0
            })
        });

        const data = await response.json();
        console.log('Manual motor response:', data);

        if (!data.success) {
            console.error('Motor error:', data.error || 'Onbekende fout');
        }
    } catch (err) {
        console.error('Fout bij manual motor command:', err);
    }
}

function initializeSpeedControl() {
    const display   = document.getElementById('speed-display');
    const btnDown   = document.getElementById('btn-speed-down');
    const btnUp     = document.getElementById('btn-speed-up');

    // Als deze pagina geen speed control heeft, doe niets
    if (!display || !btnDown || !btnUp) {
        return;
    }

    console.log('Speed control gevonden – knoppen gekoppeld');

    // Zorg dat display klopt bij start
    display.textContent = currentSpeedLevel.toString();

    btnDown.addEventListener('click', () => {
        if (currentSpeedLevel > 0) {
            currentSpeedLevel -= 1;
            display.textContent = currentSpeedLevel.toString();
            console.log('Nieuwe speed level:', currentSpeedLevel);
        }
    });

    btnUp.addEventListener('click', () => {
        if (currentSpeedLevel < 10) {
            currentSpeedLevel += 1;
            display.textContent = currentSpeedLevel.toString();
            console.log('Nieuwe speed level:', currentSpeedLevel);
        }
    });
}

// =====================
// Encoder en potmeter (manual page)
// =====================

function initializeManualSensors() {
    const encoderEl = document.getElementById('encoder-value');
    const potEl = document.getElementById('potmeter-value');

    // Als deze pagina geen sensorvelden heeft: niks doen
    if (!encoderEl && !potEl) return;

    console.log('Manual sensors gevonden, start polling...');

    // Direct 1x updaten
    updateManualSensors(encoderEl, potEl);

    // Daarna elke 250ms
    setInterval(() => {
        updateManualSensors(encoderEl, potEl);
    }, 250);
}

async function updateManualSensors(encoderEl, potEl) {
    if (encoderEl) {
        try {
            const response = await fetch('/api/encoder', { cache: 'no-store' });
            if (!response.ok) throw new Error('HTTP ' + response.status);

            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Encoder API error');

            const mm = Number(data.position_mm);
            encoderEl.textContent = Number.isFinite(mm) ? mm.toFixed(1) + ' mm' : '–';
        } catch (err) {
            console.error('Fout bij lezen positie:', err);
            encoderEl.textContent = '–';
        }
    }
    // Potmeter
    if (potEl) {
        try {
            const response = await fetch('/api/potmeter', { cache: 'no-store' });
            if (!response.ok) throw new Error('HTTP ' + response.status);

            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Potmeter API error');

            const value = Number(data.value);
            potEl.textContent = Number.isFinite(value) ? String(Math.round(value)) : '–';
        } catch (err) {
            console.error('Fout bij lezen potmeter waarde:', err);
            potEl.textContent = '–'; // of '#'
        }
    }
}
// =====================
// Homing knop (minimal)
// =====================

let homingRunning = false;
let homingPollTimer = null;

function setHomeBtnActive(btn, active) {
  // active = donker
  btn.classList.toggle('bg-gray-800', active);
  btn.classList.toggle('text-white', active);
  btn.classList.toggle('hover:bg-gray-900', active);

  // inactive = wit
  btn.classList.toggle('bg-white', !active);
  btn.classList.toggle('text-black', !active);
  btn.classList.toggle('hover:bg-gray-200', !active);
}

async function getHomingStatus() {
  const res = await fetch('/api/homing/status', { cache: 'no-store' });
  const data = await res.json();
  if (!res.ok || !data.success) throw new Error(data.error || 'status failed');
  return data; // {running: bool, last_result: ...}
}

function startHomingPolling(btn) {
  if (homingPollTimer) clearInterval(homingPollTimer);

  homingPollTimer = setInterval(async () => {
    try {
      const status = await getHomingStatus();

      // status.running false => klaar/cancel/error
      if (!status.running) {
        homingRunning = false;
        setHomeBtnActive(btn, false);

        clearInterval(homingPollTimer);
        homingPollTimer = null;
      }
    } catch (e) {
      console.error('Homing status error:', e);
      // We laten de knop in actieve state, want motor kan nog lopen.
    }
  }, 200);
}

async function startHoming() {
  const res = await fetch('/api/homing/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  const data = await res.json();
  if (!res.ok || !data.success) throw new Error(data.error || 'Homing start failed');
}

async function cancelHoming() {
  const res = await fetch('/api/homing/cancel', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  const data = await res.json();
  if (!res.ok || !data.success) throw new Error(data.error || 'Homing cancel failed');
}

function initializeHomingButton() {
  const btn = document.getElementById('home-btn');
  if (!btn) return;

  // Bij laden: check status zodat de kleur klopt als homing al bezig was
  getHomingStatus()
    .then(status => {
      homingRunning = !!status.running;
      setHomeBtnActive(btn, homingRunning);
      if (homingRunning) startHomingPolling(btn);
    })
    .catch(() => { /* geen probleem */ });

  btn.addEventListener('click', async () => {
    try {
      if (!homingRunning) {
        // start
        await startHoming();
        homingRunning = true;
        setHomeBtnActive(btn, true);
        startHomingPolling(btn);
      } else {
        // cancel
        await cancelHoming();
        // knop blijft nog even donker tot polling ziet dat running=false is
      }
    } catch (e) {
      console.error('Homing click error:', e);
      alert('Homing fout: ' + e.message);

      // Veilig: status opnieuw ophalen zodat UI klopt
      try {
        const status = await getHomingStatus();
        homingRunning = !!status.running;
        setHomeBtnActive(btn, homingRunning);
        if (homingRunning) startHomingPolling(btn);
      } catch {}
    }
  });
}

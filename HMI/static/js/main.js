// Main JavaScript file voor alle pagina's
// Transport HMI functionaliteit

// Wacht tot de DOM geladen is
document.addEventListener('DOMContentLoaded', function() {
    console.log('Main.js geladen');
    
    // Initialiseer dropdown functionaliteit
    initializeDropdowns();
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
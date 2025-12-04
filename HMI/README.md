# Transport Systeem HMI - Basic Setup

Een eenvoudige web-gebaseerde HMI voor het transport systeem, gemaakt met Flask, HTML en Tailwind CSS.

## Project Structuur

HMI/  
├── .venv/               # Virtuele Python omgeving  
├── node_modules/        # Node modules voor Tailwind  
├── src/  
│   └── input.css        # Tailwind input file  
├── static/  
│   └── css/  
│       └── tailwind.css # Gebouwde Tailwind CSS  
├── templates/  
│   └── index.html       # Hoofd HTML pagina  
├── app.py               # Flask server  
├── package.json         # NPM configuratie voor Tailwind  
├── package-lock.json    # Exacte NPM dependencies  
├── README.md            # Project uitleg  
└── requirements.txt     # Python dependencies (Flask)

## Installatie en Starten

### Stap 1: Activeer de virtuele omgeving
```
.venv\Scripts\Activate.ps1
```

### Stap 2: Installeer Flask
```
pip install -r requirements.txt
```

### Stap 3: Start Tailwind in watch-modus tijdens het ontwikkelen
```
npx @tailwindcss/cli -i ./src/input.css -o ./static/css/tailwind.css --watch
```

Dit commando bouwt Tailwind automatisch opnieuw bij elke wijziging in de HTML of input.css.  
Hierdoor blijft de styling altijd up-to-date zonder dat je handmatig opnieuw hoeft te builden.

### Stap 4: Start de server (in een tweede terminal)
```
python app.py
```

### Stap 5: Open in browser
http://localhost:5000

## Wat doet het nu?

Eenvoudige Flask webserver  
Een HTML pagina met basis styling via Tailwind  
Klaar om later uit te breiden

## Volgende stappen

Toevoegen van knoppen voor besturing  
Status indicatoren  
Integratie met Raspberry Pi GPIO  
Meerdere pagina's  
Kiosk-modus op de Raspberry Pi

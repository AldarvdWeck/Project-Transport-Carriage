import csv
import os
from dataclasses import dataclass
from typing import Dict

STATIONS_FILE = "data/stations.csv"
CSV_HEADER = ["id", "naam", "positie", "richting"]


@dataclass
class Station:
    id: int
    naam: str
    positie: int
    richting: str  # "L" or "R"

    def __post_init__(self):
        if self.richting.upper() not in ("L", "R"):
            raise ValueError("Richting moet 'L' of 'R' zijn.")
        self.richting = self.richting.upper()


def _ensure_file():
    """Creëert een geldig stations.csv bestand als het nog niet bestaat."""
    if not os.path.exists(os.path.dirname(STATIONS_FILE)):
        os.makedirs(os.path.dirname(STATIONS_FILE))

    if not os.path.exists(STATIONS_FILE):
        with open(STATIONS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)


def _write_all(stations: Dict[int, Station]):
    """Overschrijft de CSV met alle stations, gesorteerd op ID."""
    with open(STATIONS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()

        for st in sorted(stations.values(), key=lambda s: s.id):
            writer.writerow({
                "id": st.id,
                "naam": st.naam,
                "positie": st.positie,
                "richting": st.richting,
            })


def load_stations() -> Dict[int, Station]:
    """Laadt stations uit CSV en geeft dict {id: Station} terug."""
    _ensure_file()

    stations = {}
    with open(STATIONS_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                station = Station(
                    id=int(row["id"]),
                    naam=row["naam"],
                    positie=int(row["positie"]),
                    richting=row["richting"]
                )
                stations[station.id] = station
            except Exception as e:
                print(f"⚠ Waarschuwing: fout in CSV regel: {row} - {e}")
    return stations


def add_station(station: Station) -> bool:
    """Voegt een nieuw station toe. ID moet uniek zijn."""
    stations = load_stations()

    if station.id in stations:
        raise ValueError(f"Station-ID {station.id} bestaat al.")

    stations[station.id] = station
    _write_all(stations)

    return True


def remove_station(station_id: int) -> bool:
    """Verwijdert een station op ID. Retourneert True als succesvol."""
    stations = load_stations()

    if station_id not in stations:
        return False

    del stations[station_id]
    _write_all(stations)

    return True

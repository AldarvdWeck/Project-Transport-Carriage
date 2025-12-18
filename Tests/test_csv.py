from core.stations import Station, add_station, remove_station, load_stations

# Nieuw station toevoegen
add_station(Station(id=2, naam="Invoer", positie=12000, richting="L"))

# Station verwijderen
remove_station(2)

print(load_stations())

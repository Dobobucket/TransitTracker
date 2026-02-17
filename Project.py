import requests
import time
from datetime import datetime



TRAIN_LINES = {"JVL", "HVL", "WRL", "MEL", "KPL"}

API_KEY = "HDbjQ6XhJm5xWwErkdes061zkiV7WDOd7eI00Qky"
STOPS = ["5459","4459","KHAN"]

URL = "https://api.opendata.metlink.org.nz/v1/stop-predictions"

headers = {
    "accept": "application/json",
    "x-api-key": API_KEY
}


def get_data_for_stop(stop_id):
    params = {"stop_id": stop_id}
    r = requests.get(URL, headers=headers, params=params)
    r.raise_for_status()
    return r.json().get("departures", [])


def minutes_until(timestr):
    if not timestr:
        return None

    bus_time = datetime.fromisoformat(timestr)
    now = datetime.now(bus_time.tzinfo)
    diff = (bus_time - now).total_seconds() / 60
    return max(0, int(diff))


def display():
    while True:
        try:
            all_departures = []

            # fetch data for each stop separately
            for stop_id in STOPS:
                departures = get_data_for_stop(stop_id)
                for dep in departures:
                    expected = dep["departure"]["expected"]
                    aimed = dep["departure"]["aimed"]
                    time_str = expected or aimed
                    mins = minutes_until(time_str)
                    if mins is not None and mins >= 0:
                        all_departures.append((mins, dep))

            # sort by soonest departure
            all_departures.sort(key=lambda x: x[0])

            print("\033[2J\033[H")
            print("=== LIVE DEPARTURES ===\n")

            for mins, dep in all_departures[:10]:
                route = dep["service_id"]
                dest = dep["trip_headsign"]
                status = dep.get("status") or "scheduled"
                mode = "TRAIN" if route in TRAIN_LINES else " BUS "
                
                # For buses, only include route 24
                if mode == "BUS" and route != "24":
                    continue

                eta = "Due" if mins == 0 else f"{mins} min"
                print(f"[{mode}] {route:>6} → {dest:<20} {eta:>6} [{status}]")

        except Exception as e:
            print("Error:", e)

        time.sleep(15)



if __name__ == "__main__":
    display()

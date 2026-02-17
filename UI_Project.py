import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import QTimer
import requests
from datetime import datetime

TRAIN_LINES = {"JVL", "HVL", "WRL", "MEL", "KPL"}
API_KEY = "HDbjQ6XhJm5xWwErkdes061zkiV7WDOd7eI00Qky"
STOPS = ["5459","4459","KHAN"]
URL = "https://api.opendata.metlink.org.nz/v1/stop-predictions"
headers = {"accept": "application/json", "x-api-key": API_KEY}

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

class LiveDepartures(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Metlink Live Departures")
        self.resize(700, 400)

        self.layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Mode", "Route", "Destination", "ETA", "Status"])
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        # Timer to update every 15 seconds
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_departures)
        self.timer.start(15000)

        self.update_departures()

    def update_departures(self):
        LIMIT = 10  # max number of departures to display
        all_departures = []
        try:
            for stop_id in STOPS:
                departures = get_data_for_stop(stop_id)
                for dep in departures:
                    route = dep["service_id"]
                    mode = "TRAIN" if route in TRAIN_LINES else "BUS"
                    if mode == "BUS" and route != "24":
                        continue
                    expected = dep["departure"]["expected"]
                    aimed = dep["departure"]["aimed"]
                    time_str = expected or aimed
                    mins = minutes_until(time_str)
                    if mins is not None and mins >= 0:
                        all_departures.append((mins, dep, mode))

            all_departures.sort(key=lambda x: (x[1]["trip_headsign"], x[0]))
            self.table.setRowCount(len(all_departures))

            for row, (mins, dep, mode) in enumerate(all_departures):
                dest = dep["trip_headsign"]
                route = dep["service_id"]
                status = dep.get("status") or "scheduled"
                eta = "Due" if mins == 0 else f"{mins} min"

                self.table.setItem(row, 0, QTableWidgetItem(mode))
                self.table.setItem(row, 1, QTableWidgetItem(route))
                self.table.setItem(row, 2, QTableWidgetItem(dest))
                self.table.setItem(row, 3, QTableWidgetItem(eta))
                self.table.setItem(row, 4, QTableWidgetItem(status))

        except Exception as e:
            print("Error fetching departures:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LiveDepartures()
    window.show()
    sys.exit(app.exec())

import sys
import requests
from datetime import datetime
from collections import defaultdict
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel, QHeaderView
)
from PyQt6.QtCore import QTimer

API_KEY = "HDbjQ6XhJm5xWwErkdes061zkiV7WDOd7eI00Qky"
STOPS = ["5459", "4459", "KHAN"]
TRAIN_LINES = {"JVL", "HVL", "WRL", "MEL", "KPL"}
URL = "https://api.opendata.metlink.org.nz/v1/stop-predictions"
HEADERS = {"accept": "application/json", "x-api-key": API_KEY}
MAX_PER_DEST = 5  # max departures shown per group

# Map headings to lists of destinations
DEST_GROUPS = {
    "To Johnsonville": ["Johnsonville", "Broadmeadows"],
    "To Wellington": ["Wellington", "Courtney Place", "Miramar Heights", "Kilbernie"]
}

class TransitApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Departures")
        self.setGeometry(200, 200, 900, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tables = {}  # dictionary to hold tables per heading

        # Create a table for each destination group
        for heading in DEST_GROUPS.keys():
            label = QLabel(f"=== {heading} ===")
            label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px;")
            self.layout.addWidget(label)

            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels(["Mode", "Route", "From → To", "ETA", "Status", "Expected (Scheduled)"])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.layout.addWidget(table)

            self.tables[heading] = table

        # Timer to refresh departures
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_departures)
        self.timer.start(15000)  # every 15 seconds

        self.update_departures()

    def get_data_for_stop(self, stop_id):
        params = {"stop_id": stop_id}
        r = requests.get(URL, headers=HEADERS, params=params)
        r.raise_for_status()
        return r.json().get("departures", [])

    def minutes_until(self, timestr):
        if not timestr:
            return None
        bus_time = datetime.fromisoformat(timestr)
        now = datetime.now(bus_time.tzinfo)
        diff = (bus_time - now).total_seconds() / 60
        return max(0, int(diff))

    def update_departures(self):
        all_departures = []

        # Fetch departures from all stops
        for stop_id in STOPS:
            try:
                deps = self.get_data_for_stop(stop_id)
                for dep in deps:
                    expected = dep["departure"]["expected"]
                    aimed = dep["departure"]["aimed"]
                    time_str = expected or aimed
                    mins = self.minutes_until(time_str)
                    if mins is not None and mins >= 0:
                        all_departures.append((mins, dep))
            except Exception as e:
                print(f"Error fetching stop {stop_id}: {e}")

        # Group departures by destination heading
        grouped = defaultdict(list)
        for mins, dep in all_departures:
            trip_dest = dep["trip_headsign"]
            for heading, dest_list in DEST_GROUPS.items():
                if trip_dest in dest_list:
                    grouped[heading].append((mins, dep))
                    break

        # Fill tables
        for heading, table in self.tables.items():
            departures = grouped.get(heading, [])
            departures.sort(key=lambda x: x[0])
            table.setRowCount(min(len(departures), MAX_PER_DEST))

            for row, (mins, dep) in enumerate(departures[:MAX_PER_DEST]):
                route = dep["service_id"]
                status = dep.get("status") or "scheduled"
                mode = "TRAIN" if route in TRAIN_LINES else "BUS"
                eta = "Due" if mins == 0 else f"{mins} min"
                from_to = f"{dep.get('stop_id', '')} → {dep['trip_headsign']}"

                expected = dep["departure"].get("expected")
                aimed = dep["departure"].get("aimed")

                # show only HH:MM
                expected_time = datetime.fromisoformat(expected).strftime("%H:%M") if expected else "--"
                aimed_time = datetime.fromisoformat(aimed).strftime("%H:%M") if aimed else "--"

                time_display = f"{expected_time} ({aimed_time})"


                table.setItem(row, 0, QTableWidgetItem(mode))
                table.setItem(row, 1, QTableWidgetItem(route))
                table.setItem(row, 2, QTableWidgetItem(from_to))
                table.setItem(row, 3, QTableWidgetItem(eta))
                table.setItem(row, 4, QTableWidgetItem(status))
                table.setItem(row, 5, QTableWidgetItem(time_display))



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransitApp()
    window.show()
    sys.exit(app.exec())

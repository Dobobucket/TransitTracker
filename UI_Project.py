import sys
import requests
from datetime import datetime
from collections import defaultdict
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea
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
        self.setGeometry(200, 200, 550, 600)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Scroll area for all departures
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll)

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
        # Clear previous
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

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
                error_label = QLabel(f"Error fetching stop {stop_id}: {e}")
                self.scroll_layout.addWidget(error_label)

        # Group departures by destination heading
        grouped = defaultdict(list)
        for mins, dep in all_departures:
            trip_dest = dep["trip_headsign"]
            for heading, dest_list in DEST_GROUPS.items():
                if trip_dest in dest_list:
                    grouped[heading].append((mins, dep))
                    break

        # Display each group
        for heading, departures in grouped.items():
            if not departures:
                continue

            heading_label = QLabel(f"=== {heading} ===")
            heading_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px;")
            self.scroll_layout.addWidget(heading_label)

            # Sort by soonest departure
            departures.sort(key=lambda x: x[0])

            for mins, dep in departures[:MAX_PER_DEST]:
                route = dep["service_id"]
                status = dep.get("status") or "scheduled"
                mode = "TRAIN" if route in TRAIN_LINES else "BUS"
                eta = "Due" if mins == 0 else f"{mins} min"
                dep_label = QLabel(f"[{mode}] {route:>6} → {dep['trip_headsign']:<20} {eta:>6} [{status}]")
                dep_label.setStyleSheet("margin-left: 15px;")
                self.scroll_layout.addWidget(dep_label)

        # Add stretch so layout doesn't shrink
        self.scroll_layout.addStretch()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TransitApp()
    window.show()
    sys.exit(app.exec())

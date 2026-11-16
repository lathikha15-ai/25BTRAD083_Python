import unittest
from datetime import date, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import app, validate_appointment_slot


class AvailabilityValidationTests(unittest.TestCase):
    def setUp(self):
        self.doctor = {"available_days": "Mon, Tue, Wed, Fri"}

    def next_weekday(self, weekday):
        today = date.today()
        days_ahead = (weekday - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return today + timedelta(days=days_ahead)

    def test_valid_working_day_and_time(self):
        monday = self.next_weekday(0)
        self.assertIsNone(
            validate_appointment_slot(self.doctor, monday.isoformat(), "10:30")
        )

    def test_rejects_non_working_day(self):
        thursday = self.next_weekday(3)
        self.assertIn(
            "not available",
            validate_appointment_slot(self.doctor, thursday.isoformat(), "10:30")
        )

    def test_rejects_before_opening(self):
        monday = self.next_weekday(0)
        self.assertIn(
            "9:00 AM",
            validate_appointment_slot(self.doctor, monday.isoformat(), "08:30")
        )

    def test_rejects_after_closing(self):
        monday = self.next_weekday(0)
        self.assertIn(
            "9:00 AM",
            validate_appointment_slot(self.doctor, monday.isoformat(), "17:30")
        )

    def test_rejects_past_date(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        self.assertIn(
            "past",
            validate_appointment_slot(self.doctor, yesterday, "10:00")
        )


if __name__ == "__main__":
    unittest.main()

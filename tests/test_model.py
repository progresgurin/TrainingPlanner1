import unittest

from training_planner.model import (
    Training,
    TrainingBook,
    ValidationError,
    validate_date,
    validate_duration,
    validate_training_type,
)


class ValidationTests(unittest.TestCase):
    def test_valid_date(self):
        self.assertEqual(validate_date("30.04.2026"), "30.04.2026")

    def test_invalid_date_format(self):
        with self.assertRaises(ValidationError):
            validate_date("2026-04-30")

    def test_invalid_calendar_date(self):
        with self.assertRaises(ValidationError):
            validate_date("31.02.2026")

    def test_valid_duration(self):
        self.assertEqual(validate_duration("45"), 45)

    def test_invalid_duration(self):
        for value in ["0", "-5", "abc", ""]:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validate_duration(value)

    def test_training_type_required(self):
        with self.assertRaises(ValidationError):
            validate_training_type("   ")


class TrainingBookTests(unittest.TestCase):
    def test_add_and_filter(self):
        book = TrainingBook()
        book.add(Training.create("30.04.2026", "Бег", 45))
        book.add(Training.create("01.05.2026", "Силовая", 60))

        self.assertEqual(len(book.filter(training_type="бег")), 1)
        self.assertEqual(len(book.filter(date="01.05.2026")), 1)
        self.assertEqual(book.total_duration(), 105)

    def test_json_roundtrip_shape(self):
        training = Training.create("30.04.2026", "Йога", 30)
        raw = training.to_dict()
        restored = Training.from_dict(raw)

        self.assertEqual(restored.date, "30.04.2026")
        self.assertEqual(restored.training_type, "Йога")
        self.assertEqual(restored.duration, 30)


if __name__ == "__main__":
    unittest.main()

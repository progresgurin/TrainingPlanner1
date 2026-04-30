import tempfile
import unittest
from pathlib import Path

from training_planner.model import Training, TrainingBook
from training_planner.storage import JsonStorage, StorageError


class JsonStorageTests(unittest.TestCase):
    def test_missing_file_returns_empty_book(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = JsonStorage(Path(tmp) / "trainings.json")
            self.assertEqual(storage.load().all(), [])

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trainings.json"
            storage = JsonStorage(path)
            book = TrainingBook([Training.create("30.04.2026", "Бег", 45)])

            storage.save(book)
            loaded = storage.load()

            self.assertEqual(len(loaded.all()), 1)
            self.assertEqual(loaded.all()[0].training_type, "Бег")

    def test_invalid_json_raises_storage_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "trainings.json"
            path.write_text("{bad json", encoding="utf-8")
            storage = JsonStorage(path)

            with self.assertRaises(StorageError):
                storage.load()


if __name__ == "__main__":
    unittest.main()

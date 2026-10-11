import unittest
from datetime import date
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.main import list_contacts, list_upcoming_birthdays
from app.models import Contact


class ContactSearchAndBirthdayTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def add_contact(self, first_name, last_name, email, birthday):
        contact = Contact(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone="555-0100",
            birthday=birthday,
        )
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def test_search_matches_first_name_last_name_or_email(self):
        ada = self.add_contact("Ada", "Lovelace", "ada@example.com", date(1815, 12, 10))
        grace = self.add_contact("Grace", "Hopper", "grace@example.com", date(1906, 12, 9))

        def search(term):
            return list_contacts(
                search=term,
                first_name=None,
                last_name=None,
                email=None,
                db=self.db,
            )

        self.assertEqual(search("ada"), [ada])
        self.assertEqual(search("HOPPER"), [grace])
        self.assertEqual(search("EXAMPLE.COM"), [ada, grace])

    def test_upcoming_birthdays_cover_seven_day_window_across_new_year(self):
        today = self.add_contact("Today", "Birthday", "today@example.com", date(1990, 12, 30))
        last_day = self.add_contact("Sixth", "Day", "sixth@example.com", date(1990, 1, 5))
        outside = self.add_contact("Seventh", "Day", "seventh@example.com", date(1990, 1, 6))

        with patch("app.main.date") as mocked_date:
            mocked_date.today.return_value = date(2024, 12, 30)
            upcoming = list_upcoming_birthdays(self.db)

        self.assertEqual(upcoming, [today, last_day])
        self.assertNotIn(outside, upcoming)


if __name__ == "__main__":
    unittest.main()

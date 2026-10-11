import unittest
from datetime import date

from pydantic import ValidationError

from app.schemas import ContactCreate, ContactRead, ContactUpdate


class ContactSchemaTests(unittest.TestCase):
    def setUp(self):
        self.valid_contact = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "phone": "+441234567890",
            "birthday": "1815-12-10",
        }

    def test_create_schema_validates_and_parses_fields(self):
        contact = ContactCreate(**self.valid_contact, extra_data="Notes")

        self.assertEqual(contact.birthday, date(1815, 12, 10))
        self.assertEqual(contact.email, "ada@example.com")
        self.assertEqual(contact.extra_data, "Notes")

    def test_create_schema_rejects_invalid_email_and_date(self):
        with self.assertRaises(ValidationError):
            ContactCreate(**{**self.valid_contact, "email": "not-an-email"})
        with self.assertRaises(ValidationError):
            ContactCreate(**{**self.valid_contact, "birthday": "not-a-date"})

    def test_create_schema_rejects_blank_required_strings_and_unknown_fields(self):
        with self.assertRaises(ValidationError):
            ContactCreate(**{**self.valid_contact, "first_name": "  "})
        with self.assertRaises(ValidationError):
            ContactCreate(**{**self.valid_contact, "unexpected": True})

    def test_update_schema_supports_partial_updates_but_rejects_null_required_fields(self):
        update = ContactUpdate(first_name="  Ada  ")

        self.assertEqual(update.model_dump(exclude_unset=True), {"first_name": "Ada"})
        with self.assertRaises(ValidationError):
            ContactUpdate(first_name=None)
        self.assertIsNone(ContactUpdate(extra_data=None).extra_data)

    def test_read_schema_builds_from_attributes(self):
        contact = ContactRead.model_validate(
            {
                "id": 1,
                **self.valid_contact,
                "birthday": date(1815, 12, 10),
                "extra_data": None,
            }
        )

        self.assertEqual(contact.id, 1)
        self.assertEqual(contact.birthday, date(1815, 12, 10))


if __name__ == "__main__":
    unittest.main()

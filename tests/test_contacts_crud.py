import unittest

from fastapi import HTTPException
from fastapi.routing import APIRoute
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.main import (
    app,
    create_contact,
    delete_contact,
    get_contact,
    list_contacts,
    update_contact,
)
from app.schemas import ContactCreate, ContactUpdate


class ContactCrudTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.contact_data = {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": "ada@example.com",
            "phone": "+441234567890",
            "birthday": "1815-12-10",
        }

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def create_sample_contact(self):
        return create_contact(ContactCreate(**self.contact_data), self.db)

    def test_create_list_and_get_contact(self):
        created = self.create_sample_contact()

        self.assertEqual(created.id, 1)
        self.assertEqual(
            list_contacts(
                search=None,
                first_name=None,
                last_name=None,
                email=None,
                db=self.db,
            ),
            [created],
        )
        self.assertEqual(get_contact(created.id, self.db), created)

        with self.assertRaises(HTTPException) as error:
            get_contact(999, self.db)
        self.assertEqual(error.exception.status_code, 404)

    def test_update_contact_changes_only_supplied_fields(self):
        created = self.create_sample_contact()

        updated = update_contact(created.id, ContactUpdate(first_name="Augusta"), self.db)

        self.assertEqual(updated.first_name, "Augusta")
        self.assertEqual(updated.last_name, "Lovelace")
        self.assertEqual(updated.email, "ada@example.com")

    def test_delete_contact_and_missing_contact_responses(self):
        created = self.create_sample_contact()

        response = delete_contact(created.id, self.db)

        self.assertEqual(response.status_code, 204)
        with self.assertRaises(HTTPException) as error:
            delete_contact(created.id, self.db)
        self.assertEqual(error.exception.status_code, 404)

    def test_duplicate_email_returns_conflict(self):
        self.create_sample_contact()
        duplicate = ContactCreate(
            **{**self.contact_data, "first_name": "Grace", "phone": "+15555555555"}
        )

        with self.assertRaises(HTTPException) as error:
            create_contact(duplicate, self.db)
        self.assertEqual(error.exception.status_code, 409)

    def test_create_and_delete_routes_use_expected_status_codes(self):
        route_statuses = {
            (method, route.path): route.status_code
            for route in app.routes
            if isinstance(route, APIRoute)
            for method in route.methods
        }

        self.assertEqual(route_statuses[("POST", "/contacts")], 201)
        self.assertEqual(route_statuses[("DELETE", "/contacts/{contact_id}")], 204)


if __name__ == "__main__":
    unittest.main()

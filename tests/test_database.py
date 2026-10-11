import unittest
from unittest.mock import patch

from sqlalchemy import Date

from app.database import get_db
from app.models import Contact


class DatabaseTests(unittest.TestCase):
    def test_contact_model_has_required_fields_and_unique_email(self):
        columns = Contact.__table__.columns

        self.assertEqual(
            set(columns.keys()),
            {
                "id",
                "first_name",
                "last_name",
                "email",
                "phone",
                "birthday",
                "extra_data",
            },
        )
        self.assertIsInstance(columns["birthday"].type, Date)
        self.assertTrue(columns["email"].unique)
        self.assertTrue(columns["extra_data"].nullable)

    def test_database_dependency_closes_session(self):
        class StubSession:
            closed = False

            def close(self):
                self.closed = True

        session = StubSession()
        with patch("app.database.SessionLocal", return_value=session):
            dependency = get_db()
            self.assertIs(next(dependency), session)
            dependency.close()

        self.assertTrue(session.closed)

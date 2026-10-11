from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Contact
from app.schemas import ContactCreate, ContactRead, ContactUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Contacts API",
    description="A REST API for managing contacts.",
    lifespan=lifespan,
)


def upcoming_birthday_date(birthday: date, today: date, days: int = 7) -> date | None:
    """Return the birthday's occurrence in [today, today + days), if any."""
    for offset in range(days):
        occurrence = today + timedelta(days=offset)
        if (occurrence.month, occurrence.day) == (birthday.month, birthday.day):
            return occurrence
    return None


def commit_contact(db: Session, contact: Contact) -> Contact:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A contact with this email already exists.",
        ) from exc
    db.refresh(contact)
    return contact


@app.post(
    "/contacts",
    response_model=ContactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    contact = Contact(**payload.model_dump())
    db.add(contact)
    return commit_contact(db, contact)


@app.get("/contacts", response_model=list[ContactRead])
def list_contacts(
    search: str | None = Query(default=None, min_length=1),
    first_name: str | None = Query(default=None, min_length=1),
    last_name: str | None = Query(default=None, min_length=1),
    email: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
):
    statement = select(Contact)
    if search:
        pattern = f"%{search}%"
        statement = statement.where(
            or_(
                Contact.first_name.ilike(pattern),
                Contact.last_name.ilike(pattern),
                Contact.email.ilike(pattern),
            )
        )
    for field, value in (
        (Contact.first_name, first_name),
        (Contact.last_name, last_name),
        (Contact.email, email),
    ):
        if value:
            statement = statement.where(field.ilike(f"%{value}%"))
    return db.scalars(statement.order_by(Contact.id)).all()


@app.get("/contacts/birthdays", response_model=list[ContactRead])
def list_upcoming_birthdays(db: Session = Depends(get_db)):
    today = date.today()
    upcoming = []
    for contact in db.scalars(select(Contact)):
        occurrence = upcoming_birthday_date(contact.birthday, today)
        if occurrence is not None:
            upcoming.append((occurrence, contact))
    upcoming.sort(key=lambda item: (item[0], item[1].first_name, item[1].last_name))
    return [contact for _, contact in upcoming]


@app.get("/contacts/{contact_id}", response_model=ContactRead)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found.")
    return contact


@app.patch("/contacts/{contact_id}", response_model=ContactRead)
@app.put("/contacts/{contact_id}", response_model=ContactRead)
def update_contact(
    contact_id: int,
    payload: ContactUpdate,
    db: Session = Depends(get_db),
):
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, field, value)
    return commit_contact(db, contact)


@app.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found.")
    db.delete(contact)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

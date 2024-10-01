import jwt
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login, app
from flask_login import UserMixin
from hashlib import md5
from datetime import datetime, timezone
from time import time
from typing import Optional
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    user_city: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    user_city_code: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except Exception as e:
            return
        return db.session.get(User, id)

    def __repr__(self):
        return '<User {}>'.format(self.username)


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))


class MeetingInfo(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    meeting_entity: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    meeting_type: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True)
    meeting_date: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True)
    meeting_time: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True)
    # UUID of json object, stored in app
    meeting_agenda: so.Mapped[str] = so.mapped_column(sa.String(32), nullable=True)
    # Agenda Filename
    agenda_name: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True)
    meeting_minutes: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True)
    audio_name: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True)


class MeetingAttendance(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    entity_code: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    meeting_id: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    member_id: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    # Staff or member
    member_type: so.Mapped[str] = so.mapped_column(sa.String(64), nullable=True)
    # single char (n is absent, y is present
    member_present: so.Mapped[str] = so.mapped_column(sa.String(1), nullable=True)


class MeetingMotionVotes(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    entity_code: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    meeting_id: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    member_id: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    motion_id: so.Mapped[str] = so.mapped_column(sa.String(64))


class MeetingMotionItems(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    entity_code: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    meeting_id: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    motion_title: so.Mapped[str] = so.mapped_column(sa.String(64))
    agenda_item: so.Mapped[str] = so.mapped_column(sa.String(64))


class EntityGroups(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    group_type: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    group_code: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    entity_code: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)


class EntityMembers(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    group_code: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    member_first_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    member_last_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    entity_code: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    title: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    position: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    start_date: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=True)
    end_date: so.Mapped[datetime] = so.mapped_column(sa.DateTime, nullable=True)


class EntityName(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    entity_name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    entity_code: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)


class PromptInfo(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    prompt_file: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)
    meeting_id: so.Mapped[str] = so.mapped_column(sa.String(64), index=True)


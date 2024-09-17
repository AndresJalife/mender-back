from sqlalchemy.orm import relationship
from datetime import date, datetime
from src.config.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, UniqueConstraint, TypeDecorator, Float, BigInteger

metadata = Base.metadata

class FormattedDate(TypeDecorator):
    impl = Date

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%d/%m/%Y').date()
            except ValueError:
                raise ValueError("Date must be in 'dd/mm/yyyy' format")
        return value

    def process_result_value(self, value, dialect):
        return value.strftime('%d/%m/%Y') if value else None


class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True, name="user_id", autoincrement=True)
    uid = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    admin = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    created_date = Column(FormattedDate, name="created_date", default=date.today())
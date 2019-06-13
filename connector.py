from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine, ARRAY, Table

DATABASE_URI = 'postgres+psycopg2://yyewnihweunzvh:2e8441c2493a744cd9ee7b9ad46edb969f6ec7508ed9cf884d24904705b2f4a1' \
               '@ec2-50-19-221-38.compute-1.amazonaws.com:5432/ddvm01l0cr0rqa'
db = create_engine(DATABASE_URI)

Base = declarative_base()
Session = sessionmaker(bind=db)

# create a Session
session = Session()


class User(Base):
    __tablename__ = 'themes'
    user_id = Column(Integer, primary_key=True, unique=True)
    counts = Column(Integer, default=0)



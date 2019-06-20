from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, create_engine, ARRAY, Table

DATABASE_URI = 'postgres+psycopg2://cwyzqcibwgfibp:35c8357e58aae1f7f11a8c7d9683f4043c44524f83309af717293fda96292462' \
               '@ec2-54-221-214-3.compute-1.amazonaws.com:5432/dccefmk7lklpi1'
db = create_engine(DATABASE_URI)

Base = declarative_base()
Session = sessionmaker(bind=db)

# create a Session
session = Session()


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, unique=True)
    counts = Column(Integer, default=0)
    max_count = Column(Integer, default=2)


Base.metadata.create_all(db)

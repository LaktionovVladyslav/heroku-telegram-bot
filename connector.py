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
    daily_limit = Column(Integer, default=1)
    user_name = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    payed = Column(Integer, default=0)
    ref_count = Column(Integer, default=0)

    def __init__(self, user):
        self.user_id = user.id
        self.user_name = user.username
        self.first_name = user.first_name
        self.last_name = user.last_name
        session.add(self)
        session.commit()

    def add_count(self):
        self.counts += 1
        session.commit()
        return self.counts

    def add_ref_count(self):
        self.ref_count += 1
        session.commit()

    def check(self):
        valid_count = self.ref_count + self.daily_limit + self.payed
        return (valid_count - self.counts) > 0

    def add_ref_user(self, user_id):
        if not session.query(User).get(user_id):
            self.add_ref_count()
            return True
        else:
            return False


Base.metadata.create_all(db)

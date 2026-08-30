from app.db.base import Base
from app.db.session import engine
def init_db():
    #create all database table
    Base.metadata.create_all(bind=engine)
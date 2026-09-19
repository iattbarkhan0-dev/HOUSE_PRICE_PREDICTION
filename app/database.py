from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker,declarative_base 
DataBase_URL="sqlite:///./house_price.db" 
engine=create_engine(DataBase_URL,connect_args={"check_same_thread":False}) 
Sessionlocal=sessionmaker(autocommit=False,autoflush=False,bind=engine) 
Base=declarative_base() 
def get_db(): 
    db=Sessionlocal() 
    try: 
        yield db 
    finally: 
        db.close()  
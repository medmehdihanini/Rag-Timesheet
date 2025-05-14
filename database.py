import os
from sqlalchemy import create_engine, Column, String, Integer, Boolean, LargeBinary, ForeignKey, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost/backup")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Profile(Base):
    __tablename__ = "_profile"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    
    project_profiles = relationship("ProjectProfile", back_populates="profile")

class Project(Base):
    __tablename__ = "_project"
    
    idproject = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(String(1000))
    state = Column(Boolean, default=True)
    image = Column(LargeBinary, nullable=True)
    status = Column(String(50))
    
    project_profiles = relationship("ProjectProfile", back_populates="project")

class ProjectProfile(Base):
    __tablename__ = "project_profile"
    
    id = Column(Integer, primary_key=True)
    mandaybudget = Column(Float)
    consumedmandaybudget = Column(Float, default=0.0)
    project_id = Column(Integer, ForeignKey("_project.idproject"), name="project_id")
    profile_id = Column(Integer, ForeignKey("_profile.id"), name="profile_id")
    
    project = relationship("Project", back_populates="project_profiles")
    profile = relationship("Profile", back_populates="project_profiles")
    tasks = relationship("Task", back_populates="profile")

class Task(Base):
    __tablename__ = "_task"
    
    id = Column(Integer, primary_key=True)
    datte = Column(String(255))
    nb_jour = Column(Float, name="nbJour")  # Using name parameter to map to actual DB column
    text = Column(Text)
    work_place = Column(String(255), name="workPlace")  # Using name parameter to map to actual DB column
    profile_id = Column(Integer, ForeignKey("project_profile.id"))
    
    profile = relationship("ProjectProfile", back_populates="tasks")

# Helper function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

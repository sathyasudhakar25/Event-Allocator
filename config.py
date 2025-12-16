class Config:
    SECRET_KEY = "secure-local-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///events.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

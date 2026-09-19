# database.py
# ─────────────────────────────────────────────────────────────────────────────
# Like AppDbContext.cs in .NET Entity Framework
# Handles: database connection, session management, table creation
# ─────────────────────────────────────────────────────────────────────────────
#
# .NET equivalent:
#   public class AppDbContext : DbContext {
#       protected override void OnConfiguring(DbContextOptionsBuilder b)
#           => b.UseSqlite("Data Source=students.db");
#   }

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import Config

# Like: services.AddDbContext<AppDbContext>(o => o.UseSqlite("..."))
engine = create_engine(Config.DATABASE_URL, echo=False)

# Like: the base class all Entity models inherit from
Base = declarative_base()

# Like: new AppDbContext() factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Like: using (var db = new AppDbContext()) { ... }
    Opens DB session, gives it, then closes safely.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Like: db.Database.EnsureCreated()
    Creates all tables if they don't already exist.
    """
    from models import Student  # avoid circular import
    Base.metadata.create_all(bind=engine)
    print("[DB] Tables created / verified OK.")

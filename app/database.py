from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.invoice import Base
import os

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./invoices.db")

# 创建数据库引擎
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
if "sqlite" in DATABASE_URL:
    # 为SQLite添加UTF-8编码支持
    connect_args.update({
        "check_same_thread": False,
        "isolation_level": None,
    })

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # 设置为True可以看到SQL语句
    pool_pre_ping=True
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
Database Engine - 数据库引擎管理器

负责管理 SQLAlchemy Engine 和 Session 的创建
支持多种数据库（SQLite、MySQL、PostgreSQL等）
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import DeclarativeMeta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DatabaseEngine:
    """
    数据库引擎管理器 - 管理 SQLAlchemy Engine 和 Session

    特性：
    - 自动创建数据库文件目录（SQLite）
    - 连接池管理
    - 多线程支持
    - 连接健康检查
    """

    def __init__(self, db_url: str, echo: bool = False):
        """
        初始化数据库引擎

        Args:
            db_url: 数据库连接 URL
                - SQLite: sqlite:///path/to/database.db
                - MySQL: mysql+pymysql://user:pass@host:port/dbname
                - PostgreSQL: postgresql://user:pass@host:port/dbname
            echo: 是否打印 SQL 日志（调试用）
        """
        # 确保数据库文件目录存在（仅 SQLite）
        if db_url.startswith("sqlite:///"):
            db_path = Path(db_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建 SQLAlchemy Engine
        # 配置选项：
        # - echo: 打印 SQL 语句（调试用）
        # - pool_pre_ping: 连接前检查连接是否有效
        # - check_same_thread: SQLite 多线程支持
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False

        self.engine = create_engine(
            db_url, echo=echo, pool_pre_ping=True, connect_args=connect_args
        )

        # 创建 Session 工厂
        # Session 是数据库操作的主要接口
        self.session_factory = sessionmaker(
            autocommit=False,  # 手动提交事务
            autoflush=False,  # 手动刷新
            bind=self.engine,  # 绑定到引擎
        )

        logger.info(f"数据库引擎已初始化: {db_url}")

    def get_session(self) -> Session:
        """
        获取数据库会话

        每次调用都会创建一个新的 Session 实例。
        使用完毕后应该调用 session.close() 关闭会话。

        Returns:
            Session: SQLAlchemy 会话对象

        Example:
            session = engine.get_session()
            try:
                # 数据库操作
                result = session.query(Model).all()
                session.commit()
            finally:
                session.close()
        """
        return self.session_factory()

    def create_tables(self, orm_base: DeclarativeMeta):
        """
        创建所有表

        根据 OrmBase 的元数据创建数据库表结构。
        如果表已存在，不会重复创建。

        Args:
            orm_base: OrmBase 类（包含所有模型的元数据）

        Example:
            from src.common.dataaccess import OrmBase
            engine.create_tables(OrmBase)
        """
        orm_base.metadata.create_all(bind=self.engine)
        logger.info("数据库表已创建")

    def drop_tables(self, orm_base: DeclarativeMeta):
        """
        删除所有表（慎用！）

        ⚠️ 警告：此操作会删除数据库中的所有表和数据！
        仅用于测试或重置数据库。

        Args:
            orm_base: OrmBase 类（包含所有模型的元数据）
        """
        orm_base.metadata.drop_all(bind=self.engine)
        logger.warning("⚠️ 数据库表已删除")

    def dispose(self):
        """
        释放数据库连接池

        关闭所有连接并释放资源。
        通常在应用程序关闭时调用。
        """
        self.engine.dispose()
        logger.info("数据库连接池已释放")

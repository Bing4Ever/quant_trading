"""
ORM Base - SQLAlchemy 声明式基类

所有数据库模型都继承自 OrmBase
"""

from sqlalchemy.ext.declarative import declarative_base

# 创建 ORM 基类
# 所有业务模型和缓存模型都应该继承这个基类
OrmBase = declarative_base()

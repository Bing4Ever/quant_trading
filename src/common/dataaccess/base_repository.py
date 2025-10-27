"""
Base Repository - 仓储基类

提供通用的 CRUD 操作，所有业务 Repository 继承此类
"""

from typing import TypeVar, Generic, Type, List, Optional, Any, Dict
from sqlalchemy.orm import Session
from .orm_base import OrmBase

# 定义泛型类型，T 必须是 OrmBase 的子类
T = TypeVar("T", bound=OrmBase)


class BaseRepository(Generic[T]):
    """
    Repository 基类 - 提供通用的数据库操作

    所有业务 Repository 都继承这个类，获得基础的 CRUD 能力。
    使用泛型保证类型安全。

    Example:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: Session):
                super().__init__(User, session)

            def find_by_email(self, email: str) -> Optional[User]:
                return self.find_one_by(email=email)
    """

    def __init__(self, model: Type[T], session: Session):
        """
        初始化仓储

        Args:
            model: ORM 模型类（如 BacktestResult, StockData）
            session: SQLAlchemy Session
        """
        self.model = model
        self.session = session

    # ==================== 创建 ====================

    def add(self, entity: T) -> T:
        """
        添加单个实体到数据库

        Args:
            entity: 模型实例

        Returns:
            添加后的实体（包含自动生成的ID等）

        Example:
            user = User(name="Alice", email="alice@example.com")
            saved_user = repository.add(user)
            print(saved_user.id)  # 自动生成的ID
        """
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def add_all(self, entities: List[T]) -> List[T]:
        """
        批量添加实体

        性能优于多次调用 add()，因为只提交一次事务。

        Args:
            entities: 模型实例列表

        Returns:
            添加后的实体列表
        """
        self.session.add_all(entities)
        self.session.commit()
        for entity in entities:
            self.session.refresh(entity)
        return entities

    # ==================== 查询 ====================

    def get_by_id(self, entity_id: Any) -> Optional[T]:
        """
        根据主键 ID 查询单个实体

        Args:
            entity_id: 主键ID（可以是任何类型）

        Returns:
            找到的实体，不存在则返回 None

        Example:
            user = repository.get_by_id(1)
            if user:
                print(user.name)
        """
        return self.session.query(self.model).filter(self.model.id == entity_id).first()

    def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[T]:
        """
        查询所有实体

        Args:
            limit: 限制返回数量
            offset: 跳过前N条记录（分页用）

        Returns:
            实体列表

        Example:
            # 获取前 10 条记录
            users = repository.get_all(limit=10)

            # 分页：第2页，每页10条
            users_page2 = repository.get_all(limit=10, offset=10)
        """
        query = self.session.query(self.model)

        if offset:
            query = query.offset(offset)

        if limit:
            query = query.limit(limit)

        return query.all()

    def find_by(self, **filters) -> List[T]:
        """
        根据条件查询（返回多条）

        Args:
            **filters: 过滤条件，如 symbol='AAPL', strategy_name='MA'

        Returns:
            符合条件的实体列表

        Example:
            # 查找所有 AAPL 的记录
            results = repository.find_by(symbol='AAPL')

            # 查找特定策略的记录
            results = repository.find_by(
                symbol='AAPL',
                strategy_name='MovingAverage'
            )
        """
        query = self.session.query(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        return query.all()

    def find_one_by(self, **filters) -> Optional[T]:
        """
        根据条件查询（返回单条）

        Args:
            **filters: 过滤条件

        Returns:
            找到的第一个实体，不存在则返回 None

        Example:
            user = repository.find_one_by(email='alice@example.com')
        """
        query = self.session.query(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        return query.first()

    def count(self, **filters) -> int:
        """
        统计记录数

        Args:
            **filters: 过滤条件（可选）

        Returns:
            记录总数

        Example:
            # 统计所有用户
            total = repository.count()

            # 统计特定条件的记录
            active_count = repository.count(is_active=True)
        """
        query = self.session.query(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        return query.count()

    def exists(self, **filters) -> bool:
        """
        检查是否存在符合条件的记录

        Args:
            **filters: 过滤条件

        Returns:
            存在返回 True，否则返回 False

        Example:
            if repository.exists(email='alice@example.com'):
                print("Email already exists")
        """
        return self.count(**filters) > 0

    # ==================== 更新 ====================

    def update(self, entity: T) -> T:
        """
        更新实体

        Args:
            entity: 要更新的实体（必须是从数据库查询得到的）

        Returns:
            更新后的实体

        Example:
            user = repository.get_by_id(1)
            user.name = "New Name"
            repository.update(user)
        """
        self.session.merge(entity)
        self.session.commit()
        return entity

    def update_by_id(self, entity_id: Any, **updates) -> Optional[T]:
        """
        根据 ID 更新字段

        Args:
            entity_id: 实体ID
            **updates: 要更新的字段和值

        Returns:
            更新后的实体，不存在则返回 None

        Example:
            user = repository.update_by_id(1, name="New Name", age=30)
        """
        entity = self.get_by_id(entity_id)
        if entity:
            for key, value in updates.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            self.session.commit()
            self.session.refresh(entity)
        return entity

    # ==================== 删除 ====================

    def delete(self, entity: T) -> bool:
        """
        删除实体

        Args:
            entity: 要删除的实体

        Returns:
            成功返回 True
        """
        self.session.delete(entity)
        self.session.commit()
        return True

    def delete_by_id(self, entity_id: Any) -> bool:
        """
        根据 ID 删除实体

        Args:
            entity_id: 实体 ID

        Returns:
            成功返回 True，不存在返回 False
        """
        entity = self.get_by_id(entity_id)
        if entity:
            return self.delete(entity)
        return False

    def delete_by(self, **filters) -> int:
        """
        根据条件批量删除

        Args:
            **filters: 过滤条件

        Returns:
            删除的记录数

        Example:
            # 删除所有未激活的用户
            deleted_count = repository.delete_by(is_active=False)
        """
        query = self.session.query(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)

        count = query.count()
        query.delete(synchronize_session=False)
        self.session.commit()

        return count

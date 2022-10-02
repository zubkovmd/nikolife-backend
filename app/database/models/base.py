import typing

import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, text, ForeignKey, Table, Float
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


association_users_groups = Table(
    "assoc_users_groups",
    Base.metadata,
    Column("users_id", ForeignKey("users.id")),
    Column("groups_id", ForeignKey("groups.id")),
)

association_recipes_categories = Table(
    "assoc_recipes_categories",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id")),
    Column("category_id", ForeignKey("recipe_categories.id")),
)

association_recipes_groups = Table(
    "assoc_recipes_groups",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id")),
    Column("group_id", ForeignKey("groups.id")),
)

association_recipes_compilations = Table(
    "assoc_recipes_compilations",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id")),
    Column("group_id", ForeignKey("recipe_compilations.id")),
)

association_recipes_likes = Table(
    "assoc_recipes_likes",
    Base.metadata,
    Column("user_id", ForeignKey("users.id")),
    Column("recipe_id", ForeignKey("recipes.id")),
)

association_ingredients_groups = Table(
    "assoc_ingredients_groups",
    Base.metadata,
    Column("ingredients_group_id", ForeignKey("ingredients_groups.id")),
    Column("ingredients_id", ForeignKey("ingredients.id")),
)


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    registration_date = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    last_active_time = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    info = Column(String, nullable=False)           # Доп инфа о пользователе (скорее всего будет должность)
    image = Column(String, nullable=True)
    jwt = Column(String, nullable=True)
    groups = relationship("Groups", back_populates="users", secondary=association_users_groups)
    messages_send = relationship("ChatMessages", foreign_keys="ChatMessages.sender_id", back_populates="sender", cascade="all, delete")
    messages_received = relationship("ChatMessages", foreign_keys="ChatMessages.receiver_id", back_populates="receiver", cascade="all, delete")
    created_recipes = relationship("Recipes", cascade="all, delete", passive_deletes=True, lazy="select" )
    liked_recipes = relationship("Recipes", secondary=association_recipes_likes, back_populates="liked_by", cascade="all, delete")

    # def __repr__(self) -> str:
    #     return self._repr(
    #         id=self.id,
    #         username=self.username,
    #         email=self.email,
    #         groups=self.groups,
    #     )
    #
    # def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
    #     '''
    #     Helper for __repr__
    #     '''
    #     field_strings = []
    #     at_least_one_attached_attribute = False
    #     for key, field in fields.items():
    #         try:
    #             field_strings.append(f'{key}={field!r}')
    #         except sqlalchemy.orm.exc.DetachedInstanceError:
    #             field_strings.append(f'{key}=DetachedInstanceError')
    #         else:
    #             at_least_one_attached_attribute = True
    #     if at_least_one_attached_attribute:
    #         return f"<{self.__class__.__name__}({','.join(field_strings)})>"
    #     return f"<{self.__class__.__name__} {id(self)}>"


class Groups(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    users = relationship("Users", back_populates="groups", secondary=association_users_groups)

    def __repr__(self) -> str:
        return self._repr(
            id=self.id,
            name=self.name
        )

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        '''
        Helper for __repr__
        '''
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


class ChatMessages(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id",), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id",), nullable=False)
    sender = relationship("Users", foreign_keys=[sender_id], back_populates="messages_send")
    receiver = relationship("Users", foreign_keys=[receiver_id], back_populates="messages_received")

    def __repr__(self) -> str:
        return self._repr(
            id=self.id,
            sender_id=self.sender_id,
            receiver_id=self.receiver_id,
            sender=self.sender,
            receiver=self.receiver
        )

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        '''
        Helper for __repr__
        '''
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


class IngredientsGroups(Base):
    __tablename__ = "ingredients_groups"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    ingredients = relationship("Ingredients", back_populates="groups", secondary=association_ingredients_groups)

    def __repr__(self) -> str:
        return self._repr(
            id=self.id,
            name=self.name,
            ingredients=self.ingredients
        )

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        '''
        Helper for __repr__
        '''
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


class Ingredients(Base):
    __tablename__ = "ingredients"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    groups = relationship("IngredientsGroups", back_populates="ingredients", secondary=association_ingredients_groups)
    recipes = relationship("RecipeIngredients", back_populates="ingredient")

    def __repr__(self) -> str:
        return self._repr(
            id=self.id,
            name=self.name,
            groups=self.groups,
            recipes=self.recipes
        )

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        '''
        Helper for __repr__
        '''
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


class RecipeDimensions(Base):
    __tablename__ = "recipe_dimensions"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)

    def __repr__(self) -> str:
        return self._repr(
            id=self.id,
            name=self.name
        )

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        '''
        Helper for __repr__
        '''
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


class RecipeIngredients(Base):
    __tablename__ = "recipe_ingredients"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    ingredient = relationship("Ingredients", back_populates="recipes")
    value = Column(Float, nullable=False)
    dimension_id = Column(Integer, ForeignKey("recipe_dimensions.id"), nullable=False)
    dimension = relationship("RecipeDimensions")
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)

    def __repr__(self) -> str:
        return self._repr(
            id=self.id,
            ingredient_id=self.ingredient_id,
            ingredient=self.ingredient,
            value=self.value,
            dimension_id=self.dimension,
            dimension=self.dimension,
            recipe_id=self.recipe_id
        )

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        '''
        Helper for __repr__
        '''
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


class RecipeCompilations(Base):
    __tablename__ = "recipe_compilations"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    image = Column(String, nullable=True)
    recipes = relationship("Recipes", secondary=association_recipes_compilations, )


class RecipeCategories(Base):
    __tablename__ = "recipe_categories"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    recipes = relationship("Recipes", secondary=association_recipes_categories, back_populates="categories")

    def __repr__(self) -> str:
        return self._repr(
            id=self.id,
            name=self.name,
            recipes=self.recipes
        )

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        '''
        Helper for __repr__
        '''
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


class RecipeSteps(Base):
    __tablename__ = "recipe_steps"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    step_num = Column(Integer, primary_key=True, nullable=False)
    content = Column(String, nullable=False)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    recipe = relationship("Recipes", back_populates="steps")

    def __repr__(self) -> str:
        return self._repr(
            id=self.id,
            step_num=self.step_num,
            content=self.content,
            recipe_id=self.recipe_id,
            recipe=self.recipe
        )

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        '''
        Helper for __repr__
        '''
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


class Recipes(Base):
    __tablename__ = "recipes"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    title = Column(String, nullable=False)
    image = Column(String, nullable=True)
    time = Column(Integer, nullable=False)
    complexity = Column(String, nullable=False)
    servings = Column(Integer, nullable=False)
    steps = relationship("RecipeSteps", cascade="all, delete")
    categories = relationship("RecipeCategories", secondary=association_recipes_categories, back_populates="recipes")
    ingredients = relationship("RecipeIngredients", cascade="all, delete")
    allowed_groups = relationship("Groups", secondary=association_recipes_groups)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("Users", back_populates="created_recipes")
    liked_by = relationship("Users", secondary=association_recipes_likes, back_populates="liked_recipes")

    # def __repr__(self) -> str:
    #     return self._repr(
    #         id=self.id,
    #         title=self.title,
    #         image=self.image,
    #         time=self.time,
    #         complexity=self.complexity,
    #         servings=self.servings,
    #         steps=self.steps,
    #         categories=self.categories,
    #         ingredients=self.ingredients,
    #         allowed_groups=self.allowed_groups,
    #         user_id=self.user_id,
    #         user=self.user,
    #         liked_by=self.liked_by
    #     )

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        '''
        Helper for __repr__
        '''
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"


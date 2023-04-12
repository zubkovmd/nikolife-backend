"""
Module contains sqlalchemy models for entire service.
"""
import datetime
from typing import Optional, TypeVar, List

from fastapi import HTTPException
import sqlalchemy
from sqlalchemy import Column, Integer, String, DateTime, text, ForeignKey, Table, Float
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base, relationship, selectinload
from starlette import status

from app.api.routes.default_response_models import GroupWithExpirationTime, DefaultResponse
from app.api.routes.v1.recipes.utility_classes import CreateRecipeIngredientRequestModel

Base = declarative_base()

"""
    Association table for MANY-TO-MANY Users-Groups models.
    Implement user grouping like 'admin', 'user', etc..
"""
association_users_groups = Table(
    "assoc_users_groups",
    Base.metadata,
    Column("users_id", ForeignKey("users.id")),
    Column("groups_id", ForeignKey("groups.id")),
    Column("expiration_time", DateTime(timezone=True), nullable=True)
)

"""
    Association table for MANY-TO-MANY Recipes-RecipeCategories models.
    Implement recipe categories like 'breakfast', 'lunch', etc...
"""
association_recipes_categories = Table(
    "assoc_recipes_categories",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id")),
    Column("category_id", ForeignKey("recipe_categories.id")),
)

"""
    Association table for MANY-TO-MANY Recipes-Groups models.
    Implement accessing to recipe for users with specific groups. Default 'user' have access to one
    list of recipes, 'approved_user' to other...
"""
association_recipes_groups = Table(
    "assoc_recipes_groups",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id")),
    Column("group_id", ForeignKey("groups.id")),
)

"""
    Association table for MANY-TO-MANY Recipes-RecipesCompilations models.
    Implement compilations of recipes. Admins can group recipes, then name it, add image and
    it's called compilation of recipes.
"""
association_recipes_compilations = Table(
    "assoc_recipes_compilations",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipes.id")),
    Column("group_id", ForeignKey("recipe_compilations.id", ondelete="RESTRICT")),
)

"""
    Association table for MANY-TO-MANY Users-Recipes models.
    Implement table that contains recipes liked by user.
"""
association_recipes_likes = Table(
    "assoc_recipes_likes",
    Base.metadata,
    Column("user_id", ForeignKey("users.id")),
    Column("recipe_id", ForeignKey("recipes.id")),
)

"""
    Association table for MANY-TO-MANY Users-Recipes models.
    Implement ingredient grouping. Like apple can have groups 'fruits', 'sugar' (contain sugar), etc..
"""
association_ingredients_groups = Table(
    "assoc_ingredients_groups",
    Base.metadata,
    Column("ingredients_group_id", ForeignKey("ingredients_groups.id")),
    Column("ingredients_id", ForeignKey("ingredients.id")),
)


UsersTypeVar = TypeVar("UsersTypeVar", bound="Users")
RecipesTypeVar = TypeVar("RecipesTypeVar", bound="Recipes")
RecipeIngredientsTypeVar = TypeVar("RecipeIngredientsTypeVar", bound="RecipeIngredients")
RecipeCategoriesTypeVar = TypeVar("RecipeCategoriesTypeVar", bound="RecipeCategories")
ChatMessagesTypeVar = TypeVar("ChatMessagesTypeVar", bound="ChatMessages")
ArticlesTypeVar = TypeVar("ArticlesTypeVar", bound="Articles")
IngredientsGroupsTypeVar = TypeVar("IngredientsGroupsTypeVar", bound="IngredientsGroups")
IngredientsTypeVar = TypeVar("IngredientsTypeVar", bound="Ingredients")
RecipeDimensionsTypeVar = TypeVar("RecipeDimensionsTypeVar", bound="RecipeDimensions")
GroupsTypeVar = TypeVar("GroupsTypeVar", bound="Groups")


class Users(Base):
    """
    User model.

    Description: Default user model that most services have.

    Example:
        Let's register a new user:
        new_user = Users(
            username="user_username",
            password="user_password",
            email="user_email@gmail.com",
            name="Default Uesr",
            info="Newbie user",
            iamge="/user_username/user_image.jpg"
        )
        groups, messages, recipes and articles foreign models will be explained later in this file. See specific
        model for description and examples
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """user id  (primary key, autogenerate)"""
    registration_date = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    """user registration date, (autogenerate)"""
    last_active_time = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    """user last active time (autogenerate, autoupdate)"""
    username = Column(String, nullable=False)
    """user username"""
    password = Column(String, nullable=False)
    """user password"""
    email = Column(String, nullable=False)
    """user email"""
    name = Column(String, nullable=False)
    """user name"""
    info = Column(String, nullable=False)           # Доп инфа о пользователе (скорее всего будет должность)
    """user info, like job_title, position """
    image = Column(String, nullable=True)
    """path to user image in s3-compatible service. (i used minio, result like 'USERNAME/IMAGE_NAME.jpg')"""
    groups = relationship("Groups", back_populates="users", secondary=association_users_groups)
    """List of user groups"""
    messages_send: List[ChatMessagesTypeVar] = relationship("ChatMessages", foreign_keys="ChatMessages.sender_id",
                                                            back_populates="sender", cascade="all, delete")
    """List of messages send by user"""
    messages_received: List[ChatMessagesTypeVar] = relationship("ChatMessages", foreign_keys="ChatMessages.receiver_id",
                                                                back_populates="receiver", cascade="all, delete")
    """List of messages received by user"""
    created_recipes: List[RecipesTypeVar] = relationship("Recipes", cascade="all, delete", passive_deletes=True, lazy="select")
    """List of recipes created by user"""
    liked_recipes: List[RecipesTypeVar] = relationship("Recipes", secondary=association_recipes_likes, 
                                                       back_populates="liked_by", cascade="all, delete")
    """List of recipes liked by user"""
    articles: List[ArticlesTypeVar] = relationship("Articles", cascade="all, delete", passive_deletes=True)
    """List of articles created by user"""

    @hybrid_property
    def group_names(self):
        return [group.name for group in self.groups]

    @classmethod
    async def get_by_id(cls, user_id: int, session: AsyncSession, join_tables: list = ()) -> UsersTypeVar:
        """
        Method returns user object from database with search by id. If user with this id does not exist, then throws
        404_NOT_FOUND exception.

        :param user_id: user id to search.
        :param session: SQLAlchemy AsyncSession object.
        :param join_tables: what tables should be joined to user object.
        :return: User object.
        """
        stmt = (
            sqlalchemy.select(Users)
            .filter(Users.id == user_id)
            .limit(1)
        )
        if join_tables:
            for table in join_tables:
                stmt = stmt.options(selectinload(table))
        resp = await session.execute(stmt)
        user = resp.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        return user

    @classmethod
    async def get_groups_with_expiration_time(cls, user_id: int, session: AsyncSession) -> List[GroupWithExpirationTime]:
        groups_response = await session.execute(
            sqlalchemy.select(association_users_groups)
            .filter(association_users_groups.c.users_id == user_id)
        )
        groups = groups_response.fetchall()
        response: List[GroupWithExpirationTime] = []
        for group_response in groups:
            group_id: int = group_response[1]
            expiration_time: Optional[datetime.datetime] = group_response[2]
            group_model = await Groups.get_by_id(group_id=group_id, session=session)
            response.append(GroupWithExpirationTime(name=group_model.name, expiration_time=expiration_time))
        return response

    @classmethod
    async def get_all(cls, session: AsyncSession, join_tables: Optional[list] = None) -> List[UsersTypeVar]:
        """
        Method returns user object from database with search by id. If user with this id does not exist, then throws
        404_NOT_FOUND exception.

        :param session: SQLAlchemy AsyncSession object.
        :param join_tables: what tables should be joined to user object.
        :return: User object.
        """
        stmt = (
            sqlalchemy.select(Users)
            .options(selectinload(Users.groups))
        )
        if join_tables:
            stmt = stmt.options(selectinload(*join_tables))
        resp = await session.execute(stmt)
        user = resp.scalars().all()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        return user

    @classmethod
    async def get_by_username(cls, session: AsyncSession, username, join_tables: Optional[list] = None) -> UsersTypeVar:
        """
        Method returns user object from database with search by id. If user with this id does not exists, then throws
        404_NOT_FOUND exception.

        :param username:  username to search.
        :param session: SQLAlchemy AsyncSession object.
        :param join_tables: what tables should be joined to user object.
        :return: User object.
        """
        stmt = (
            sqlalchemy.select(Users)
            .where(Users.username == username)
            .limit(1)
        )
        if join_tables is not None:
            for table in join_tables:
                stmt = stmt.options(selectinload(table))
        response = await session.execute(stmt)
        user: Users = response.scalars().one()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        return user

    def __str__(self):
        """string represent of model"""
        return f"{self.username}, ({self.name}, {self.info if self.info else 'NO_INFO'})"


class Groups(Base):
    """
    Group model

    Description: Users can receive that groups (one or many).
    Example:
        Let's imagine that we register a default user_a just now. Unfortunately this user do not have
        permissions for accessing our services. So first what we need is to create group and then add
        created user to this group:
        user_a = register_user(**{credentials})
        group_for_accessing_some_content = Groups(name='default_group') | if we already have this group: get_def_group()
    """

    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """group id  (primary key, autogenerate)"""
    name = Column(String, nullable=False)
    """group name"""
    users = relationship("Users", back_populates="groups", secondary=association_users_groups)
    """users in this group"""

    def __str__(self):
        """string represent of model"""
        return self.name

    @classmethod
    async def get_by_id(cls, group_id: int, session: AsyncSession) -> Optional[GroupsTypeVar]:
        """
        Method returns group by id

        :param group_id: id of group
        :param session: SQLAlchemy AsyncSession object.
        :return: Group object if group found else None
        """
        group_stmt = sqlalchemy.select(Groups).filter(Groups.id == group_id).limit(1)
        group: Optional[Groups] = (await session.execute(group_stmt)).scalars().first()
        return group

    @classmethod
    async def update_expiration_time(cls, user_id: int, group_id: int, expiration_time: datetime.datetime, session: AsyncSession):
        """
        Method updates time of group expiration;

        :param user_id: user id
        :param group_id: group id
        :param expiration_time: new expiration time
        :return: None
        """
        await session.execute(
            sqlalchemy.update(association_users_groups)
            .values(expiration_time=expiration_time)
            .where(
                sqlalchemy.and_(
                    association_users_groups.c.users_id == user_id,
                    association_users_groups.c.groups_id == group_id
                )
            )
        )


class ChatMessages(Base):
    """
    Chat message model

    Description: Users can chat with each other's. For each message service create instance of this model.

    Example:
        user_a: Users want to send message to user_b: Users with text MESSAGE_TEXT: str = "hello, user_b
        So we need to put this message to database:
        new_message = ChatMessages(sender=user_a, receiver=user_b, text=MESSAGE_TEXT )
    """

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """chat message id  (primary key, autogenerate)"""
    sender_id = Column(Integer, ForeignKey("users.id",), nullable=False)
    """id of sender: Users"""
    receiver_id = Column(Integer, ForeignKey("users.id",), nullable=False)
    """id of receiver: Users"""
    sender = relationship("Users", foreign_keys=[sender_id], back_populates="messages_send")
    """sender link"""
    receiver = relationship("Users", foreign_keys=[receiver_id], back_populates="messages_received")
    """receiver link"""

    #  TODO: there should be added message text column and possible image.
    #   About image: Maybe i should send image link like default message
    #   and on client side regexp check it if it's image. Then depending on result show image or text.


class IngredientsGroups(Base):
    """
    Ingredient group model.

    Description: Ingredient sucha as an apple can have some ingredient groups like "fruits",
    "sugar" (contain sugar), etc.. . Service user this groups for filtering recipes when user, for example, want search
    recipes without fruit's in ingredients.
    """

    __tablename__ = "ingredients_groups"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """ingredient group id  (primary key, autogenerate)"""
    name = Column(String, nullable=False)
    """ingredient group name"""
    ingredients = relationship("Ingredients", back_populates="groups", secondary=association_ingredients_groups)
    """ingredients in this group"""

    @classmethod
    async def get_by_name_or_create(cls, name: str, session) -> IngredientsGroupsTypeVar:
        """
        Method return ingredient group by passed name. If group does not exist, then it will be created.
        For additional info check app.database.models.base -> IngredientsGroups.

        :param name: Group name.
        :param session: SQLAlchemy AsyncSession object.
        :return: Ingredient group mapped object.
        """
        stmt = sqlalchemy.select(IngredientsGroups).where(IngredientsGroups.name == name)
        response = await session.execute(stmt)
        found_group = response.scalars().first()
        if found_group:
            return found_group
        else:
            new_group = IngredientsGroups(name=name)
            session.add(new_group)
            return new_group

    def __str__(self):
        """string represent of model"""
        return self.name


class Ingredients(Base):
    """
    Ingredient model

    Description: Recipe can have one or more ingredients. By the way you should check RecipeIngredients docstring.

    Example:
        Let's create an Apple ingredient. First, to be clear (but it is not required) we need to declare a groups for
        this ingredient (service use ingredient groups for recipes filtering):
        fruits_group = IngredientsGroups(name="fruits")
        sugar_group = IngredientsGroups(name="sugar") <-- sugar group contains all ingredients with sugar in it.

        Then we can create ingredient:
        apple_ingredient = Ingredients(name="Apple", groups=[fruits_group, sugar_group])

        And now we can use apple ingredient in all recipes.
    """

    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """ingredient id  (primary key, autogenerate)"""
    name = Column(String, nullable=False)
    """ingredient name. Like apple, parrot, etc..."""
    groups = relationship("IngredientsGroups", back_populates="ingredients", secondary=association_ingredients_groups)
    """groups of this ingredient. See IngredientsGroups description"""
    recipes = relationship("RecipeIngredients", back_populates="ingredient")
    """recipes with this ingredient"""

    def __str__(self):
        """string represent of model"""
        return self.name

    @classmethod
    async def get_by_name_or_create(cls, ingredient: CreateRecipeIngredientRequestModel, session: AsyncSession) \
            -> IngredientsTypeVar:
        """
        Method return ingredient by passed name. If ingredient does not exist, then it will be created.
        Ingredient groups will be added too.
        For additional info check app.database.models.base -> Ingredients.

        :param ingredient: ingredient name.
        :param session: SQLAlchemy AsyncSession object.
        :return: Ingredient group mapped object.
        """
        stmt = sqlalchemy.select(Ingredients).where(Ingredients.name == ingredient.name)
        response = await session.execute(stmt)
        found_ingredient = response.scalars().first()
        if found_ingredient:
            return found_ingredient
        new_ingredient_model = Ingredients(name=ingredient.name.lower().capitalize())
        for group in ingredient.groups:
            group_model = await IngredientsGroups.get_by_name_or_create(group, session)
            new_ingredient_model.groups.append(group_model)
        session.add(new_ingredient_model)
        return new_ingredient_model


class RecipeDimensions(Base):
    """
    Dimensions model

    Description: Ingredients added to a recipe may vary in weight/volume even within the same ingredient.
    This model is used to associate an ingredient for a specific recipe with its dimension.
    Like weight (gr, kg, mg, ...) or volume(l, ml, ...). By the way you should check RecipeIngredients docstring.

    Example:
        new_dimension = RecipeDimensions(name="g") <--- creates grams dimension
    """

    __tablename__ = "recipe_dimensions"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """dimension id  (primary key, autogenerate)"""
    name = Column(String, nullable=False)
    """dimension name"""

    def __str__(self):
        """string represent of model"""
        return self.name

    @classmethod
    async def get_by_name_or_create(cls, dimension: str, session) -> RecipeDimensionsTypeVar:
        """
        Method return dimension by passed name. If dimension does not exist, then it will be created.
        For additional info check app.database.models.base -> RecipeDimensions.

        :param dimension: Dimension name.
        :param session: SQLAlchemy AsyncSession object.
        :return: Ingredient group mapped object.
        """
        stmt = sqlalchemy.select(RecipeDimensions).where(RecipeDimensions.name == dimension)
        response = await session.execute(stmt)
        found_dimension = response.scalars().first()
        if found_dimension:
            return found_dimension
        else:
            found_dimension = RecipeDimensions(name=dimension)
            session.add(found_dimension)
            return found_dimension


class RecipeIngredients(Base):
    """
    Recipe ingredient model.
    Description: The recipe can contain several ingredients. This model is uses **Ingredients** models for build
    recipe ingredients with specific dimension (like g/mg or l/ml) and it's value (like **5** mg or **15** ml).
    Example:

        We have to create a new recipe with ingredients Apple(15g) and Carrot(35g). First we need to create
        ingredients Apple and carrot for this. apple_ingredient=Ingredients(name='apple'...),
        carrot_ingredient=Ingredients(name='carrot'). Now we can add them to database and reuse ingredients for
        each recipe.

        Then we should create a dimensions: in example we need one dimension - grams (g). So we create this with
        grams_dimension = RecipeDimensions("g"). Now we can add this to database and reuse for each recipe.


        Within this example we should create two RecipeIngredients: apple with value 15g and carrot with value 35g.
        apple_recipe_ingredient = RecipeIngredient(
                                            ingredient=apple_ingredient,
                                            dimension=grams_dimension,
                                            value=15)
        carrot_recipe_ingredient = RecipeIngredient(
                                            ingredient=carrot_ingredient,
                                            dimension=grams_dimension,
                                            value=35)
        Now we can add these ingredients to recipe:
        RECIPE_INSTANCE.ingredients=[apple_recipe_ingredient, carrot_recipe_ingredient]
    """

    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """recipe_ingredient id  (primary key, autogenerate)"""
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    """id of ingredient: Ingredients"""
    ingredient = relationship("Ingredients", back_populates="recipes", lazy="select")
    """ingredient instance link"""
    value = Column(Float, nullable=False)
    """
    recipe value for dimenshion.

    Description: Ingredients added to a recipe may vary in weight/volume even within the same ingredient.
    This model is used to associate an ingredient for a specific recipe with its weight/volume.

    Example:carrot 14 g, there carrot is ingredient, g is dimension and 14 is value
    """
    dimension_id = Column(Integer, ForeignKey("recipe_dimensions.id"), nullable=False)
    """id of dimension: Dimension"""
    dimension = relationship("RecipeDimensions", lazy="select")
    """dimension instance link"""
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    """id of recipe: Recipes"""

    def __str__(self):
        """string represent of model"""
        return f"{str(self.ingredient)}, {self.value} {str(self.dimension)}"

    @classmethod
    async def create(cls, ingredient: CreateRecipeIngredientRequestModel, session) \
            -> RecipeIngredientsTypeVar:
        """
        Method will create RecipeIngredients object.
        For additional info check app.database.models.base -> RecipeIngredients.

        :param ingredient: Ingredient request object.
        :param session: SQLAlchemy AsyncSession object.
        :return: Created ingredient.
        """
        ingredient_model = await Ingredients.get_by_name_or_create(ingredient, session)
        dimension_model = await RecipeDimensions.get_by_name_or_create(ingredient.dimension, session)
        recipe_ingredient = RecipeIngredients(
            ingredient=ingredient_model,
            value=ingredient.weight,
            dimension=dimension_model,
        )
        return recipe_ingredient


class RecipeCompilations(Base):
    """
    Recipe compilations model.
    Description: Admins can group recipes, then name it, add image, and it's called compilation of recipes.

    Example:
        For create a new compilation, first we need some recipes. Let's think we already create some recipes and pass
        it to variables recipe_1, recipe_2, recipe_3. No we can user this model for create recipe compilation:
        new_compilation = RecipeCompilations(
            name='my awesome compilation',
            image='/MY_USERNAME/compilations/compilation_image.jpg',
            recipes=[recipe_1, recipe_2, recipe_3]
        )
    """

    __tablename__ = "recipe_compilations"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """recipes compilation id  (primary key, autogenerate)"""
    name = Column(String, nullable=False)
    """recipe compilation name"""
    image = Column(String, nullable=True)
    """path to compilation image in s3-compatible service. (i used minio, result like 'USERNAME/IMAGE_NAME.jpg')"""
    recipes = relationship("Recipes", secondary=association_recipes_compilations)
    """list recipes in this compilation"""

    def __str__(self):
        """string represent of model"""
        return self.name


class RecipeCategories(Base):
    """
    Recipe categories model

    Description: Recipes can have some categories like 'breakfast', 'snack', 'salad' and this categories can combine.
    For example, 'pancakes with jam' recipe can have 'breakfast' and 'snack' categories.

    Example:
        If we need to add new category 'snack' we can just create category with this model.
        new_category = RecipeCategories(name='snack').
        Now we can add recipes to this category or add this category to recipes:
        recipe.categories.append(new_category) | new_category.recipes.append(recipe)
    """

    __tablename__ = "recipe_categories"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    "recipe category id  (primary key, autogenerate)"
    name = Column(String, nullable=False)
    "recipe category name"
    image = Column(String, nullable=True)
    "recipe category image"
    recipes = relationship("Recipes", secondary=association_recipes_categories, back_populates="categories")
    "list of recipes with this category"

    def __str__(self):
        """string represent of model"""
        return self.name

    @classmethod
    async def get_by_id(cls, category_id: int, session: AsyncSession) -> Optional[RecipeCategoriesTypeVar]:
        """
        Method returns category by id

        :param category_id: category id
        :param session: SQLAlchemy AsyncSession object.
        :return: Category object
        """
        response = await session.execute(
            sqlalchemy.select(RecipeCategories)
            .filter(RecipeCategories.id == category_id)
            .options(selectinload(RecipeCategories.recipes))
            .limit(1)
        )
        category: RecipeCategories = response.scalars().first()
        return category

    @classmethod
    async def delete_by_id(cls, category_id: int, session: AsyncSession) -> None:
        """
        Method removes category from base

        :param category_id: category id
        :param session: SQLAlchemy AsyncSession object
        :return: None
        """
        category = await RecipeCategories.get_by_id(category_id=category_id, session=session)
        category.recipes = []
        await session.delete(category)

    @classmethod
    async def get_by_name(cls, name: str, session: AsyncSession) -> Optional[RecipeCategoriesTypeVar]:
        """
        Method search category by name

        :param name: category name
        :param session: SQLAlchemy AsyncSession object
        :return: category
        """
        response = await session.execute(
            sqlalchemy.select(RecipeCategories)
            .filter(RecipeCategories.name == name)
            .limit(1)
        )
        return response.scalars().first()

    @classmethod
    async def get_by_name_or_create(cls, name: str, session: AsyncSession) -> RecipeCategoriesTypeVar:
        """
        Method return category by passed name. If category does not exist, then it will be created.
        For additional info check app.database.models.base -> RecipeCategories.

        :param name: Dimension name.
        :param session: SQLAlchemy AsyncSession object.
        :return: Ingredient group mapped object.
        """
        category = await RecipeCategories.get_by_name(name=name, session=session)
        if category:
            return category
        else:
            category = RecipeCategories(name=name)
            return category


class RecipeSteps(Base):
    """
    Model for recipe step

    Description: Every recipe have steps that you should reproduce for cook. This model implements this steps.

    Example:
        Imagine we need to add 'applesauce' recipe. For applesauce, we need to add two steps:
        step_1_content = 'Combine apples, water, sugar, and cinnamon in a saucepan; cover
            and cook over medium heat until apples are soft, about 15 to 20 minutes.'

        step_2_content = 'Allow apple mixture to cool, then mash with a fork or potato masher until
            it is the consistency you like.'

        So we create two instances of this model:
        step_1 = RecipeSteps(step_num=1, content=step_1_content)
        step_2 = RecipeSteps(step_num=2, content=step_2_content)

        Now we can add this steps to our new recipe model (recipe_model: Recipes)
        recipe_model.steps = [step_1, step_2]
    """

    __tablename__ = "recipe_steps"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """recipe step id (primary key, autogenerate)"""
    step_num = Column(Integer, primary_key=False, nullable=False)
    """step number (1,2,3...)"""
    content = Column(String, nullable=False)
    """step content (text)"""
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    """id of recipe: Recipes"""
    recipe = relationship("Recipes", back_populates="steps")
    """Recipes model link"""

    def __str__(self):
        """string represent of model"""
        return self.content


class StoryItem(Base):
    """
    Story item model

    Description: implementation of images for story model with ONE-TO_MANY. For one story you can add
    some story items (images).

    Example:
         We just created a new_story: Story. Now we need add images:
         story_image_1 = StoryItem(image='/USERNAME/stories/STORY_ID/IMAGENAME_1.jpg')
         story_image_2 = StoryItem(image='/USERNAME/stories/STORY_ID/IMAGENAME_2.jpg')
         story_image_3 = StoryItem(image='/USERNAME/stories/STORY_ID/IMAGENAME_3.jpg')
         Now we can add this images to story:
         new_story.story_items=[story_image_1, story_image_2, story_image_3]
    """

    __tablename__ = "story_item"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """story item id (primary key, autogenerate)"""
    story_id = Column(Integer, ForeignKey("story.id"))
    """id of story: Story"""
    story = relationship("Story", back_populates="story_items")
    """Story model link"""
    image = Column(String, nullable=False)
    """path to story image in s3-compatible service. (i used minio, result like 'USERNAME/IMAGE_NAME.jpg')"""


class Story(Base):
    """
    Story model

    Description: In this service we have a stories like instagram or other social network (bubbles with user profile
    image on top of main page).
    Example:
        Creating a new story:
        new_story = Story(
            title="my new story",
            thumbnail="/USERNAME/stories/STORY_ID/thumbnail.jpg")
        story_item_1: StoryItem, story_item_2: StoryItem, story_item_3: StoryItem
        new_story.story_items=[story_item_1, story_item_2, story_item_3]
    """

    __tablename__ = "story"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """story id (primary key, autogenerate)"""
    title = Column(String, nullable=False)
    """story title"""
    thumbnail = Column(String, nullable=False)
    """path to story thumbnail in s3-compatible service. (i used minio, result like 'USERNAME/IMAGE_NAME.jpg')"""
    story_items = relationship("StoryItem", cascade="all, delete")
    """StoryItem model links"""

    def __str__(self):
        """string represent of model"""
        return self.title


class Articles(Base):
    """
    Article model

    Description: In this service admin can create an articles with news, helpful tips, etc.

    Example:
        creating a new article:
        new_article = Articles(
            title="My new article",
            subtitle="Short info",
            image="/USERNAME/stories/STORY_ID/ARTICLE_IMAGE.jpg",
            user=USER_THAT_CREATES_ARTICLE(:Users)
            text="My new article text or information"
        )
"""

    __tablename__ = "article"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """article id (primary key, autogenerate)"""
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    """time when article created (autogenerate)"""
    title = Column(String, nullable=False)
    """article title"""
    subtitle = Column(String, nullable=False)
    """article subtitle / short info"""
    image = Column(String, nullable=False)
    """path to article image in s3-compatible service. (i used minio, result like 'USERNAME/IMAGE_NAME.jpg')"""
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    """id of user: Users"""
    user = relationship("Users", back_populates="articles")
    """Users model link of user that creates this article"""
    text = Column(String, nullable=False)
    """article text"""

    def __str__(self):
        """string represent of model"""
        return self.title


class Recipes(Base):
    """
    Recipe model

    Description: Model implements recipe.

    Example:
        For recipe creation we need to create instance of Recipes model:
        new_recipe = Recipes(
            title="My awesome recipe",
            image="/USERNAME/recipes/RECIPE_ID/ARTICLE_IMAGE.jpg",
            time=65,
            complexity="semi-hard",
            servings=3,
            user=CURRENT_USER_MODEL
        )
        For recipe we can add (it is not required but expected by the service):
            1) recipe_steps: List[RecipeSteps] (check RecipeSteps model documentation)
                new_recipe.steps = recipe_steps
            2) recipe_categories: List[RecipeCategories] (check RecipeCategories documentation)
                new_recipe.categories = recipe_categories
            3) recipe_ingredients: List[RecipeIngredients] (check RecipeIngredients documentation)
                new_recipe.ingredients = recipe_ingredients
            4) recipe_allowed_groups: List[Groups] (check Groups documentation)
                new_recipe.allowed_groups = recipe_allowed_groups
    """

    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    """recipe id (primary key, autogenerate)"""
    title = Column(String, nullable=False)
    """recipe title"""
    image = Column(String, nullable=True)
    """path to recipe image in s3-compatible service. (i used minio, result like 'USERNAME/IMAGE_NAME.jpg')"""
    time = Column(Integer, nullable=False)
    """recipe cooking time"""
    complexity = Column(String, nullable=False)
    """recipe complexity (easy/medium/hard/etc...)"""
    servings = Column(Integer, nullable=False)
    """recipe servings"""
    steps = relationship("RecipeSteps", cascade="all, delete")
    """RecipeSteps model links"""
    categories = relationship("RecipeCategories", secondary=association_recipes_categories, back_populates="recipes")
    """RecipeCategories model links"""
    ingredients: List[RecipeIngredientsTypeVar] = relationship("RecipeIngredients", cascade="all, delete")
    """RecipeIngredients model links"""
    compilations = relationship(
        "RecipeCompilations",
        secondary=association_recipes_compilations,
        back_populates="recipes"
    )
    """RecipeCompilations model links"""
    allowed_groups = relationship("Groups", secondary=association_recipes_groups)
    """Groups model links"""
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    """id of user: Users"""
    user = relationship("Users", back_populates="created_recipes")
    """Users model link of user that creates this recipe"""
    liked_by = relationship("Users", secondary=association_recipes_likes, back_populates="liked_recipes")
    """Users model links of users that likes this recipe"""

    @classmethod
    async def get_by_id(cls, recipe_id: int, session: AsyncSession, join_tables: list = ()):
        """
            Method search recipe by passed id. If recipe not found, then it throws
            404_NOT_FOUND exception

            :param recipe_id: id of recipe.
            :param session: SQLAlchemy AsyncSession object.
            :return: Found recipe.
            """
        stmt = (
            sqlalchemy.select(Recipes)
            .where(Recipes.id == recipe_id)
            .limit(1)
        )
        # stmt.options(selectinload(Ingredients.groups))
        if join_tables:
            for table in join_tables:
                if type(table) in [tuple, set, list]:
                    stmt = stmt.options(selectinload(*table))
                else:
                    stmt = stmt.options(selectinload(table))
        resp = await session.execute(stmt)
        recipe: Recipes = resp.scalars().first()
        if not recipe:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рецепт не найден")
        return recipe

    @classmethod
    async def get_all_with_ingredients(
            cls,
            ingredient_names: List[str],
            session: AsyncSession
    ) -> List[RecipesTypeVar]:
        stmt = sqlalchemy.select(Recipes)
        stmt = stmt.join(RecipeIngredients).join(Ingredients)
        stmt = stmt.filter(Ingredients.name.in_(ingredient_names))
        response = await session.execute(stmt)
        recipes: List[Recipes] = response.scalars().all()
        return recipes

    @classmethod
    async def get_all_with_categories(cls, categories_names: List[str], session: AsyncSession) -> List[RecipesTypeVar]:
        stmt = sqlalchemy.select(Recipes)
        stmt = stmt.join(RecipeCategories)
        stmt = stmt.filter(RecipeCategories.name.in_(categories_names))
        response = await session.execute(stmt)
        recipes: List[Recipes] = response.scalars().all()
        return recipes

    def __str__(self):
        """string represent of model"""
        return self.title

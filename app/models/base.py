from app.db.base import Base
from app.models.mixins import TimestampMixin
class BaseModel(Base , TimestampMixin):
    # """
    # Base class for every database model.

    # Every model will automatically receive:

    # • id (we'll add later if desired)
    # • created_at
    # • updated_at
    # """
    __abstract__=True
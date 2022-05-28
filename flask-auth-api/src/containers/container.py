from dependency_injector import containers, providers

from db.cache import Caches
from db.db import Database
from repository.repository import Repositiry
from services.request import RequestService
from services.roles import RoleService
from services.users import UserService


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(modules=["api.v1.users", "api.v1.roles", "api.v1.request"])
    db = providers.Singleton(Database)

    caches = providers.Singleton(Caches)

    repository = providers.Factory(Repositiry, session_factory=db.provided.session_manager)

    user_service = providers.Factory(UserService, repository=repository, cache=caches)
    role_service = providers.Factory(RoleService, repository=repository)
    request_service = providers.Factory(RequestService, repository=repository, cache=caches)

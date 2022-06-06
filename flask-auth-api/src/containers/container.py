from dependency_injector import containers, providers

from db.cache import Caches
from db.db import Database
from repository.repository import Repositiry
from services.request import RequestService
from services.roles import RoleService
from services.users import (
    BaseUserService,
    ManageSocialUserService,
    HistoryUserService,
    RoleUserService,
    ManageUserService,
)


class Container(containers.DeclarativeContainer):

    wiring_config = containers.WiringConfiguration(modules=["api.v1.users", "api.v1.roles", "api.v1.request"])
    db = providers.Singleton(Database)

    caches = providers.Singleton(Caches)

    repository = providers.Factory(Repositiry, session_factory=db.provided.session_manager)

    base_user_service = providers.Factory(BaseUserService, repository=repository, cache=caches)
    manage_user_service = providers.Factory(ManageUserService, repository=repository, cache=caches)
    manage_social_user_service = providers.Factory(ManageSocialUserService, repository=repository, cache=caches)
    role_user_service = providers.Factory(RoleUserService, repository=repository, cache=caches)
    history_user_service = providers.Factory(HistoryUserService, repository=repository, cache=caches)

    role_service = providers.Factory(RoleService, repository=repository)
    request_service = providers.Factory(RequestService, repository=repository, cache=caches)

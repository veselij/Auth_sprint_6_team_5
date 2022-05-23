from typing import Optional

from models.db_models import Role
from repository.repository import Repositiry


class RoleService:
    def __init__(self, repository: Repositiry) -> None:
        self.repository = repository

    def create_roles(self, roles: list) -> bool:
        for role in roles:
            role = Role(role=role["role"], description=role["description"])
            if not self.repository.create_obj_in_db(role):
                return False
        return True

    def get_roles(self) -> Optional[Role]:
        return self.repository.get_objects_by_field(Role)

    def delete_role(self, role_id: str) -> bool:
        return self.repository.delete_object_by_field(Role, id=role_id)

    def update_role(self, role_id: str, fields: dict) -> bool:
        return self.repository.update_obj_in_db(Role, fileds_to_update=fields, id=role_id)

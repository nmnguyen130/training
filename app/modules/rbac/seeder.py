import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import app_engine, app_session
from app.modules.rbac.constants import ALL_PERMISSIONS, SYSTEM_ROLES
from app.modules.rbac.model import Permission, Role, RolePermission

logger = logging.getLogger(__name__)


async def seed_rbac(db: AsyncSession) -> None:
    """Idempotently seed permissions, roles, and mappings."""
    logger.info("Seeding RBAC permissions and system roles...")

    # 1. Upsert Permissions (Bulk)
    perm_values = [
        {
            "permission_code": code,
            "is_active": True,
        }
        for code in ALL_PERMISSIONS
    ]
    perm_insert_stmt = (
        pg_insert(Permission)
        .values(perm_values)
        .on_conflict_do_nothing(
            index_elements=[Permission.permission_code],
        )
    )
    await db.execute(perm_insert_stmt)
    await db.flush()

    # Load all permissions into a lookup map: code -> id
    perm_res = await db.execute(select(Permission.permission_code, Permission.permission_id))
    perm_map = dict(perm_res.all())

    # 2. Upsert System Roles
    role_values = [
        {
            "role_code": code,
            "role_name": info["role_name"],
            "description": info["description"],
            "is_system": True,
            "is_active": True,
        }
        for code, info in SYSTEM_ROLES.items()
    ]
    role_insert_stmt = (
        pg_insert(Role)
        .values(role_values)
        .on_conflict_do_update(
            index_elements=[Role.role_code],
            set_={
                "role_name": pg_insert(Role).excluded.role_name,
                "description": pg_insert(Role).excluded.description,
                "is_system": True,
            },
        )
    )
    await db.execute(role_insert_stmt)
    await db.flush()

    # Load all roles into a lookup map: code -> id
    role_res = await db.execute(select(Role.role_code, Role.role_id))
    role_map = dict(role_res.all())

    # 3. Seed Role-Permission Mappings
    rp_values = []
    for role_code, info in SYSTEM_ROLES.items():
        role_id = role_map.get(role_code)
        if not role_id:
            continue
        for res, actions in info["permissions"].items():
            for action in actions:
                perm_id = perm_map.get(f"{res}.{action}")
                if perm_id:
                    rp_values.append({"role_id": role_id, "permission_id": perm_id})

    if rp_values:
        rp_insert_stmt = (
            pg_insert(RolePermission)
            .values(rp_values)
            .on_conflict_do_nothing(
                index_elements=[RolePermission.role_id, RolePermission.permission_id]
            )
        )
        await db.execute(rp_insert_stmt)

    await db.commit()
    logger.info(
        "RBAC seed completed: %d permissions, %d system roles configured.",
        len(ALL_PERMISSIONS),
        len(SYSTEM_ROLES),
    )


async def main() -> None:
    """CLI runner for RBAC seeder."""
    logging.basicConfig(level=logging.INFO)
    async with app_session() as session:
        await seed_rbac(session)
    await app_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

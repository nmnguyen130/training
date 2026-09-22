from datetime import datetime, timezone
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ServiceError
from app.modules.auth.model import UserAccount
from app.modules.warehouse.model import Location, Warehouse
from app.modules.warehouse.schemas import (
    LocationCreate,
    LocationResponse,
    LocationTreeResponse,
    LocationUpdate,
    WarehouseCreate,
    WarehouseUpdate,
)
from app.utils.pagination import PaginationParams


class WarehouseController:
    def __init__(
        self,
        db: AsyncSession,
        current_user: UserAccount | None = None,
    ) -> None:
        self.db = db
        self.current_user = current_user

    async def get_by_id(self, warehouse_id: int, with_locations: bool = False) -> Warehouse:
        stmt = select(Warehouse).where(Warehouse.warehouse_id == warehouse_id)
        if with_locations:
            stmt = stmt.options(selectinload(Warehouse.locations))
        warehouse = await self.db.scalar(stmt)
        if not warehouse:
            raise ServiceError.not_found("Warehouse")
        return warehouse

    async def get_by_code(self, warehouse_code: str) -> Warehouse | None:
        stmt = select(Warehouse).where(
            Warehouse.warehouse_code == warehouse_code.strip().upper()
        )
        return await self.db.scalar(stmt)

    async def list_warehouses(
        self,
        pagination: PaginationParams,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Warehouse], int]:
        filters = []
        if is_active is not None:
            filters.append(Warehouse.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Warehouse.warehouse_code.ilike(pattern),
                    Warehouse.warehouse_name.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Warehouse).where(*filters)
        stmt = (
            select(Warehouse)
            .where(*filters)
            .order_by(Warehouse.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        warehouses = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(warehouses) < pagination.limit:
            total = len(warehouses)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return warehouses, total

    async def create(self, data: WarehouseCreate) -> Warehouse:
        code = data.warehouse_code.strip().upper()
        code_exists = await self.db.scalar(
            select(Warehouse.warehouse_id).where(Warehouse.warehouse_code == code)
        )
        if code_exists:
            raise ServiceError.conflict(f"Warehouse code '{code}' is already taken")

        warehouse = Warehouse(
            warehouse_code=code,
            warehouse_name=data.warehouse_name.strip(),
            address=data.address,
            description=data.description,
            is_active=data.is_active,
        )
        self.db.add(warehouse)
        await self.db.flush()
        await self.db.commit()
        return warehouse

    async def update(self, warehouse_id: int, data: WarehouseUpdate) -> Warehouse:
        warehouse = await self.get_by_id(warehouse_id)
        update_data = data.model_dump(exclude_unset=True)

        if "warehouse_code" in update_data:
            code = update_data["warehouse_code"].strip().upper()
            if code != warehouse.warehouse_code:
                code_exists = await self.db.scalar(
                    select(Warehouse.warehouse_id).where(
                        Warehouse.warehouse_code == code,
                        Warehouse.warehouse_id != warehouse_id,
                    )
                )
                if code_exists:
                    raise ServiceError.conflict(f"Warehouse code '{code}' is already taken")
            update_data["warehouse_code"] = code

        if "warehouse_name" in update_data and update_data["warehouse_name"]:
            update_data["warehouse_name"] = update_data["warehouse_name"].strip()

        for field, value in update_data.items():
            setattr(warehouse, field, value)

        warehouse.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return warehouse

    async def deactivate(self, warehouse_id: int) -> Warehouse:
        warehouse = await self.get_by_id(warehouse_id)
        warehouse.is_active = False
        warehouse.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return warehouse


class LocationController:
    def __init__(
        self,
        db: AsyncSession,
        current_user: UserAccount | None = None,
    ) -> None:
        self.db = db
        self.current_user = current_user

    async def get_by_id(self, location_id: int, with_relations: bool = False) -> Location:
        stmt = select(Location).where(Location.location_id == location_id)
        if with_relations:
            stmt = stmt.options(
                selectinload(Location.warehouse),
                selectinload(Location.parent),
                selectinload(Location.children),
            )
        location = await self.db.scalar(stmt)
        if not location:
            raise ServiceError.not_found("Location")
        return location

    async def list_by_warehouse(
        self,
        warehouse_id: int,
        parent_location_id: int | None = None,
        can_store_inventory: bool | None = None,
        is_active: bool | None = None,
    ) -> list[Location]:
        warehouse_exists = await self.db.scalar(
            select(Warehouse.warehouse_id).where(Warehouse.warehouse_id == warehouse_id)
        )
        if not warehouse_exists:
            raise ServiceError.not_found("Warehouse")

        filters = [Location.warehouse_id == warehouse_id]

        if parent_location_id is not None:
            filters.append(Location.parent_location_id == parent_location_id)
        if can_store_inventory is not None:
            filters.append(Location.can_store_inventory == can_store_inventory)
        if is_active is not None:
            filters.append(Location.is_active == is_active)

        stmt = (
            select(Location)
            .where(*filters)
            .order_by(Location.sort_order.asc(), Location.location_code.asc())
        )
        return list((await self.db.scalars(stmt)).all())

    async def get_tree(self, warehouse_id: int) -> list[LocationTreeResponse]:
        warehouse_exists = await self.db.scalar(
            select(Warehouse.warehouse_id).where(Warehouse.warehouse_id == warehouse_id)
        )
        if not warehouse_exists:
            raise ServiceError.not_found("Warehouse")

        stmt = (
            select(Location)
            .where(Location.warehouse_id == warehouse_id, Location.is_active.is_(True))
            .order_by(Location.sort_order.asc(), Location.location_code.asc())
        )
        locations = list((await self.db.scalars(stmt)).all())

        node_map: dict[int, LocationTreeResponse] = {}
        for loc in locations:
            node_map[loc.location_id] = LocationTreeResponse(
                **LocationResponse.model_validate(loc).model_dump(),
                children=[],
            )

        roots: list[LocationTreeResponse] = []
        for loc in locations:
            node = node_map[loc.location_id]
            if loc.parent_location_id is None:
                roots.append(node)
            else:
                parent_node = node_map.get(loc.parent_location_id)
                if parent_node:
                    parent_node.children.append(node)
                else:
                    roots.append(node)

        return roots

    async def _check_cycle(self, location_id: int, target_parent_id: int) -> None:
        """Check cycle detection when changing parent."""
        curr_id: int | None = target_parent_id
        visited: set[int] = set()

        while curr_id is not None:
            if curr_id == location_id:
                raise ServiceError.bad_request(
                    "Circular reference detected: cannot set parent to a descendant node"
                )
            if curr_id in visited:
                break
            visited.add(curr_id)

            curr_id = await self.db.scalar(
                select(Location.parent_location_id).where(Location.location_id == curr_id)
            )

    async def create(self, data: LocationCreate) -> Location:
        # 1. Check warehouse
        warehouse_exists = await self.db.scalar(
            select(Warehouse.warehouse_id).where(Warehouse.warehouse_id == data.warehouse_id)
        )
        if not warehouse_exists:
            raise ServiceError.not_found("Warehouse")

        # 2. Check parent if given
        if data.parent_location_id is not None:
            parent = await self.get_by_id(data.parent_location_id)
            if parent.warehouse_id != data.warehouse_id:
                raise ServiceError.bad_request(
                    "Parent location must belong to the same warehouse"
                )

        # 3. Check unique location_code in warehouse
        loc_code = data.location_code.strip()
        code_exists = await self.db.scalar(
            select(Location.location_id).where(
                Location.warehouse_id == data.warehouse_id,
                Location.location_code == loc_code,
            )
        )
        if code_exists:
            raise ServiceError.conflict(
                f"Location code '{loc_code}' is already taken in this warehouse"
            )

        # 4. Check unique barcode if provided
        barcode = data.barcode.strip() if data.barcode else None
        if barcode:
            barcode_exists = await self.db.scalar(
                select(Location.location_id).where(Location.barcode == barcode)
            )
            if barcode_exists:
                raise ServiceError.conflict(f"Barcode '{barcode}' is already taken")

        location = Location(
            warehouse_id=data.warehouse_id,
            parent_location_id=data.parent_location_id,
            location_code=loc_code,
            location_name=data.location_name.strip(),
            location_type=data.location_type.strip().upper(),
            location_purpose=data.location_purpose.strip().upper(),
            barcode=barcode,
            can_store_inventory=data.can_store_inventory,
            max_weight_kg=data.max_weight_kg,
            sort_order=data.sort_order,
            is_active=data.is_active,
        )
        self.db.add(location)
        await self.db.flush()
        await self.db.commit()
        return location

    async def update(self, location_id: int, data: LocationUpdate) -> Location:
        location = await self.get_by_id(location_id)
        update_data = data.model_dump(exclude_unset=True)

        if "parent_location_id" in update_data:
            new_parent_id = update_data["parent_location_id"]
            if new_parent_id is not None:
                if new_parent_id == location_id:
                    raise ServiceError.bad_request("Location cannot be its own parent")
                parent = await self.get_by_id(new_parent_id)
                if parent.warehouse_id != location.warehouse_id:
                    raise ServiceError.bad_request(
                        "Parent location must belong to the same warehouse"
                    )
                await self._check_cycle(location_id, new_parent_id)

        if "location_code" in update_data:
            code = update_data["location_code"].strip()
            if code != location.location_code:
                code_exists = await self.db.scalar(
                    select(Location.location_id).where(
                        Location.warehouse_id == location.warehouse_id,
                        Location.location_code == code,
                        Location.location_id != location_id,
                    )
                )
                if code_exists:
                    raise ServiceError.conflict(
                        f"Location code '{code}' is already taken in this warehouse"
                    )
            update_data["location_code"] = code

        if "barcode" in update_data:
            b_code = update_data["barcode"].strip() if update_data["barcode"] else None
            if b_code and b_code != location.barcode:
                barcode_exists = await self.db.scalar(
                    select(Location.location_id).where(
                        Location.barcode == b_code,
                        Location.location_id != location_id,
                    )
                )
                if barcode_exists:
                    raise ServiceError.conflict(f"Barcode '{b_code}' is already taken")
            update_data["barcode"] = b_code

        if "location_name" in update_data and update_data["location_name"]:
            update_data["location_name"] = update_data["location_name"].strip()

        if "location_type" in update_data and update_data["location_type"]:
            update_data["location_type"] = update_data["location_type"].strip().upper()

        if "location_purpose" in update_data and update_data["location_purpose"]:
            update_data["location_purpose"] = update_data["location_purpose"].strip().upper()

        for field, value in update_data.items():
            setattr(location, field, value)

        location.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return location

    async def deactivate(self, location_id: int) -> Location:
        location = await self.get_by_id(location_id)
        location.is_active = False
        location.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return location

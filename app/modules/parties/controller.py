from datetime import datetime, timezone
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ServiceError
from app.modules.auth.model import UserAccount
from app.modules.parties.model import Customer, Party, PartyType, Supplier
from app.modules.parties.schemas import (
    CustomerCreate,
    PartyCreate,
    PartyUpdate,
    SupplierCreate,
)
from app.modules.rbac.field_permissions import check_field_permissions
from app.utils.pagination import PaginationParams


class PartyController:
    def __init__(
        self,
        db: AsyncSession,
        current_user: UserAccount | None = None,
    ) -> None:
        self.db = db
        self.current_user = current_user

    async def get_by_id(self, party_id: int, with_relations: bool = False) -> Party:
        stmt = select(Party).where(Party.party_id == party_id)
        if with_relations:
            stmt = stmt.options(
                selectinload(Party.customer),
                selectinload(Party.supplier),
            )
        party = await self.db.scalar(stmt)
        if not party:
            raise ServiceError.not_found("Party")
        return party

    async def list_parties(
        self,
        pagination: PaginationParams,
        search: str | None = None,
        party_type: PartyType | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Party], int]:
        filters = []

        if party_type is not None:
            filters.append(Party.party_type == party_type)
        if is_active is not None:
            filters.append(Party.is_active == is_active)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Party.display_name.ilike(pattern),
                    Party.phone.ilike(pattern),
                    Party.email.ilike(pattern),
                )
            )

        count_stmt = select(func.count()).select_from(Party).where(*filters)
        stmt = (
            select(Party)
            .options(selectinload(Party.customer), selectinload(Party.supplier))
            .where(*filters)
            .order_by(Party.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )

        parties = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(parties) < pagination.limit:
            total = len(parties)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return parties, total

    async def create(self, data: PartyCreate) -> Party:
        party = Party(
            party_type=data.party_type,
            display_name=data.display_name,
            phone=data.phone,
            email=data.email,
            address=data.address,
        )
        self.db.add(party)
        await self.db.flush()
        await self.db.commit()
        return party

    async def update(self, party_id: int, data: PartyUpdate) -> Party:
        check_field_permissions(
            resource="party",
            action="update",
            role_code=getattr(self.current_user, "role_code", None),
            fields=data.model_fields_set,
        )

        party = await self.get_by_id(party_id, with_relations=True)
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(party, field, value)

        party.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return party

    async def deactivate(self, party_id: int) -> Party:
        party = await self.get_by_id(party_id, with_relations=True)
        party.is_active = False
        party.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        return party

    # Customer Operations
    async def create_customer(self, data: CustomerCreate) -> Customer:
        code_exists = await self.db.scalar(
            select(Customer.customer_id).where(Customer.customer_code == data.customer_code)
        )
        if code_exists:
            raise ServiceError.conflict(
                f"Customer code '{data.customer_code}' is already taken"
            )

        party = Party(
            party_type=data.party_type,
            display_name=data.display_name,
            phone=data.phone,
            email=data.email,
            address=data.address,
        )
        customer = Customer(party=party, customer_code=data.customer_code)
        self.db.add_all([party, customer])
        await self.db.commit()

        customer.party = party
        return customer

    async def get_customer(self, customer_id: int) -> Customer:
        stmt = (
            select(Customer)
            .where(Customer.customer_id == customer_id)
            .options(selectinload(Customer.party))
        )
        customer = await self.db.scalar(stmt)
        if not customer:
            raise ServiceError.not_found("Customer")
        return customer

    async def list_customers(
        self, pagination: PaginationParams
    ) -> tuple[list[Customer], int]:
        count_stmt = select(func.count()).select_from(Customer)
        stmt = (
            select(Customer)
            .options(selectinload(Customer.party))
            .order_by(Customer.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        items = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(items) < pagination.limit:
            total = len(items)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return items, total

    # Supplier Operations
    async def create_supplier(self, data: SupplierCreate) -> Supplier:
        code_exists = await self.db.scalar(
            select(Supplier.supplier_id).where(Supplier.supplier_code == data.supplier_code)
        )
        if code_exists:
            raise ServiceError.conflict(
                f"Supplier code '{data.supplier_code}' is already taken"
            )

        party = Party(
            party_type=data.party_type,
            display_name=data.display_name,
            phone=data.phone,
            email=data.email,
            address=data.address,
        )
        supplier = Supplier(party=party, supplier_code=data.supplier_code)
        self.db.add_all([party, supplier])
        await self.db.commit()

        supplier.party = party
        return supplier

    async def get_supplier(self, supplier_id: int) -> Supplier:
        stmt = (
            select(Supplier)
            .where(Supplier.supplier_id == supplier_id)
            .options(selectinload(Supplier.party))
        )
        supplier = await self.db.scalar(stmt)
        if not supplier:
            raise ServiceError.not_found("Supplier")
        return supplier

    async def list_suppliers(
        self, pagination: PaginationParams
    ) -> tuple[list[Supplier], int]:
        count_stmt = select(func.count()).select_from(Supplier)
        stmt = (
            select(Supplier)
            .options(selectinload(Supplier.party))
            .order_by(Supplier.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.limit)
        )
        items = list((await self.db.scalars(stmt)).all())

        if pagination.page == 1 and len(items) < pagination.limit:
            total = len(items)
        else:
            total = await self.db.scalar(count_stmt) or 0

        return items, total

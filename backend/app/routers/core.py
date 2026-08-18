from fastapi import APIRouter

from app.models.master import (
    Customer,
    Employee,
    Product,
    ProductCategory,
    UoM,
    Vendor,
    WarehouseLocation,
    Workcenter,
)
from app.routers.base import create_crud_router

router = APIRouter(prefix="/api/master", tags=["Master Data"])

router.include_router(
    create_crud_router(UoM, "/uoms", ["UoM"], order_by=UoM.name)
)
router.include_router(
    create_crud_router(ProductCategory, "/product-categories", ["Product Category"], order_by=ProductCategory.name)
)
router.include_router(
    create_crud_router(Product, "/products", ["Product"], order_by=Product.code)
)
router.include_router(
    create_crud_router(WarehouseLocation, "/locations", ["Warehouse Location"], order_by=WarehouseLocation.code)
)
router.include_router(
    create_crud_router(Customer, "/customers", ["Customer"], order_by=Customer.name)
)
router.include_router(
    create_crud_router(Vendor, "/vendors", ["Vendor"], order_by=Vendor.name)
)
router.include_router(
    create_crud_router(Workcenter, "/workcenters", ["Workcenter"], order_by=Workcenter.code)
)
router.include_router(
    create_crud_router(Employee, "/employees", ["Employee"], order_by=Employee.employee_no)
)

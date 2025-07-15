import asyncio
from app.main import app
from app.db.session import get_db
from app.modules.master_data.brands.service import BrandService
from app.modules.master_data.brands.repository import BrandRepository
from app.modules.master_data.brands.schemas import BrandFilter, BrandSort

async def test_brands_list():
    """Test the brands list method directly"""
    async for db in get_db():
        try:
            # Create repository and service
            repository = BrandRepository(db)
            service = BrandService(repository)
            
            # Test with sort object
            filters = BrandFilter(
                name=None,
                code=None,
                is_active=None,
                search=None
            )
            
            sort = BrandSort(
                field="name",
                direction="asc"
            )
            
            print("Testing list_brands with sort object...")
            result = await service.list_brands(
                page=1,
                page_size=20,
                filters=filters,
                sort=sort,
                include_inactive=False
            )
            
            print(f"Success! Found {result.total} brands")
            
        except Exception as e:
            print(f"Error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(test_brands_list())
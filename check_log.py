import asyncio, json
from src.core.database.service import db_service

async def main():
    cfg = await db_service.get_system_setting('log_settings')
    print(json.dumps(cfg, ensure_ascii=True, indent=2))

if __name__ == '__main__':
    asyncio.run(main())

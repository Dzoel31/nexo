import pytest
from db.session import engine


@pytest.fixture(autouse=True, scope="function")
async def dispose_engine_after_test():
    yield
    await engine.dispose()

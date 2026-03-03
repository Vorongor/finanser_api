import taskiq_fastapi
from taskiq_redis import RedisAsyncResultBackend, ListQueueBroker
from src.config import get_settings


settings = get_settings()


result_backend = RedisAsyncResultBackend(redis_url=settings.REDIS_URL)

broker = ListQueueBroker(url=settings.REDIS_URL).with_result_backend(
    result_backend
)

taskiq_fastapi.init(broker, "src.main:app")

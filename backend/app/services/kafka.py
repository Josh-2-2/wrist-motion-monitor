import json
import logging
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from app.config import settings

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer | None:
    global _producer
    if _producer is None:
        try:
            _producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode(),
            )
            await _producer.start()
            logger.info("Kafka producer connected to %s", settings.kafka_bootstrap_servers)
        except KafkaConnectionError:
            logger.warning("Kafka unavailable — readings will not be streamed to topic")
            _producer = None
    return _producer


async def stop_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None


async def publish_reading(session_id: int, reading: dict) -> None:
    producer = await get_producer()
    if producer is None:
        return
    try:
        await producer.send(
            settings.kafka_topic_imu,
            value={"session_id": session_id, **reading},
        )
    except Exception:
        logger.warning("Failed to publish reading to Kafka", exc_info=True)

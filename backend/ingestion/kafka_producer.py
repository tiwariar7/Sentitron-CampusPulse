import os
import json
import logging
from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)

class KafkaProducerManager:
    _producer: AIOKafkaProducer = None
    _connection_failed: bool = False
    
    @classmethod
    async def get_producer(cls) -> AIOKafkaProducer:
        if cls._connection_failed:
            raise RuntimeError("Kafka connection is marked as offline. Skipping connection attempt.")
            
        if cls._producer is None:
            KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
            try:
                # Limit bootstrap timeouts to 2 seconds to avoid blocking the event loop
                cls._producer = AIOKafkaProducer(
                    bootstrap_servers=KAFKA_BROKER,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    request_timeout_ms=2000,
                    api_version="auto"
                )
                await cls._producer.start()
                logger.info("Shared Kafka Producer started successfully.")
            except Exception as e:
                cls._connection_failed = True
                cls._producer = None
                logger.warning(f"Kafka connection attempt failed (Broker offline?): {e}")
                raise e
        return cls._producer
        
    @classmethod
    async def close_producer(cls):
        if cls._producer is not None:
            await cls._producer.stop()
            cls._producer = None
            logger.info("Shared Kafka Producer stopped.")
        cls._connection_failed = False

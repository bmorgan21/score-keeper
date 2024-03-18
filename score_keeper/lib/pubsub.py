import redis.asyncio as aioredis


class PubSubManager:
    async def connect(self) -> None:
        raise NotImplementedError()

    async def publish(self, channel_id: str, message: str) -> None:
        raise NotImplementedError()

    async def subscribe(self, channel_id: str) -> aioredis.Redis:
        raise NotImplementedError()

    async def unsubscribe(self, channel_id: str) -> None:
        raise NotImplementedError()


class RedisPubSubManager(PubSubManager):
    """
        Initializes the RedisPubSubManager.

    Args:
        host (str): Redis server host.
        port (int): Redis server port.
    """

    def __init__(self, host="localhost", port=6379):
        self.redis_host = host
        self.redis_port = port
        self.pubsub = None
        self.redis_connection = None

    async def _get_redis_connection(self) -> aioredis.Redis:
        """
        Establishes a connection to Redis.

        Returns:
            aioredis.Redis: Redis connection object.
        """
        return aioredis.Redis(
            host=self.redis_host, port=self.redis_port, auto_close_connection_pool=False
        )

    async def connect(self) -> None:
        """
        Connects to the Redis server and initializes the pubsub client.
        """
        if self.redis_connection is None:
            self.redis_connection = await self._get_redis_connection()
            self.pubsub = self.redis_connection.pubsub()

    async def publish(self, channel_id: str, message: str) -> None:
        """
        Publishes a message to a specific Redis channel.

        Args:
            channel_id (str): Channel ID.
            message (str): Message to be published.
        """
        await self.redis_connection.publish(channel_id, message)

    async def subscribe(self, channel_id: str) -> aioredis.Redis:
        """
        Subscribes to a Redis channel.

        Args:
            channel_id (str): Channel ID to subscribe to.

        Returns:
            aioredis.ChannelSubscribe: PubSub object for the subscribed channel.
        """
        await self.pubsub.subscribe(channel_id)
        return self.pubsub

    async def unsubscribe(self, channel_id: str) -> None:
        """
        Unsubscribes from a Redis channel.

        Args:
            channel_id (str): Channel ID to unsubscribe from.
        """
        await self.pubsub.unsubscribe(channel_id)

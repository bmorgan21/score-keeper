import asyncio

from quart import Websocket

from .pubsub import PubSubManager


class WebsocketManager:
    def __init__(self, pubsub_client: PubSubManager):
        """
        Initializes the WebsocketManager.

        Attributes:
            channels (dict): A dictionary to store Websocket connections in different channels.
            pubsub_client (RedisPubSubManager): An instance of the PubSubManager class
                for pub-sub functionality.
        """
        self.channels: dict = {}
        self.pubsub_client = pubsub_client
        self.task_initialized = False

    async def add_user_to_channel(self, channel_id: str, socket: Websocket) -> None:
        """
        Adds a user's Websocket connection to a channel.

        Args:
            channel_id (str): Channel ID.
            socket (Websocket): Websocket connection object.
        """
        await socket.accept()

        if channel_id in self.channels:
            self.channels[channel_id].append(socket)
        else:
            self.channels[channel_id] = [socket]

            await self.pubsub_client.connect()
            pubsub_subscriber = await self.pubsub_client.subscribe(channel_id)
            if not self.task_initialized:
                self.task_initialized = True
                asyncio.create_task(self._pubsub_data_reader(pubsub_subscriber))

    async def broadcast_to_channel(self, channel_id: str, message: str) -> None:
        """
        Broadcasts a message to all connected Websockets in a channel.

        Args:
            channel_id (str): Channel ID.
            message (str): Message to be broadcasted.
        """
        await self.pubsub_client.connect()
        await self.pubsub_client.publish(channel_id, message)

    async def remove_user_from_channel(
        self, channel_id: str, socket: Websocket
    ) -> None:
        """
        Removes a user's Websocket connection from a channel.

        Args:
            channel_id (str): Channel ID.
            websocket (Websocket): Websocket connection object.
        """
        self.channels[channel_id].remove(socket)

        if len(self.channels[channel_id]) == 0:
            del self.channels[channel_id]
            await self.pubsub_client.unsubscribe(channel_id)

    async def _pubsub_data_reader(self, pubsub_subscriber):
        """
        Reads and broadcasts messages received from PubSub.

        Args:
            pubsub_subscriber (ChannelSubscribe): PubSub object for the subscribed channel.
        """
        while True:
            message = await pubsub_subscriber.get_message(
                ignore_subscribe_messages=True
            )
            if message is not None:
                channel_id = message["channel"].decode("utf-8")
                if channel_id in self.channels:
                    all_sockets = self.channels[channel_id]
                    for socket in all_sockets:
                        data = message["data"].decode("utf-8")
                        await socket.send(data)

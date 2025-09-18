import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import ChatMessage, BlockedUser


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        self.receiver_username = self.scope["url_route"]["kwargs"]["receiver_username"]

        if not self.user or not self.user.is_authenticated:
            await self.send(text_data=json.dumps({
                "error": "Authentication tələb olunur. Token göndərin."
            }))
            await self.close()
            return

        try:
            receiver = await self.get_user(self.receiver_username)
        except User.DoesNotExist:
            await self.send(text_data=json.dumps({
                "error": "Alıcı istifadəçi tapılmadı"
            }))
            await self.close()
            return

        if self.user.username == self.receiver_username:
            await self.send(text_data=json.dumps({
                "error": "Özünüzlə chat edə bilməzsiniz"
            }))
            await self.close()
            return

        self.room_name = self.get_room_name(self.user.username, self.receiver_username)

        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

        await self.accept()

        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": f"Bağlantı uğurla quruldu. {self.receiver_username} ilə chat edə bilərsiniz.",
            "room": self.room_name,
            "sender": self.user.username,
            "receiver": self.receiver_username
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(
                self.room_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()

            # Yeni: mark_read tipi üçün xüsusi sorğu
            if data.get("type") == "mark_read":
                message_ids = data.get("message_ids", [])
                updated = await self.mark_multiple_as_read(message_ids)
                await self.send(text_data=json.dumps({
                    "type": "read_confirmation",
                    "updated_messages": updated
                }))
                return

            if not message:
                await self.send(text_data=json.dumps({
                    "error": "Mesaj boş ola bilməz"
                }))
                return

            sender = self.user
            receiver = await self.get_user(self.receiver_username)

            if await self.is_blocked(sender.username, receiver.username):
                await self.send(text_data=json.dumps({
                    "error": "Bu istifadəçi sizi blok edib"
                }))
                return

            chat = await self.create_message(sender, receiver, message)

            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender": sender.username,
                    "receiver": receiver.username,
                    "timestamp": str(chat.created_at),
                    "message_id": chat.id,
                    "is_read": chat.is_read,
                }
            )

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "error": "Yanlış JSON formatı"
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": f"Xəta: {str(e)}"
            }))

    async def chat_message(self, event):
        is_read = event["is_read"]

        # Əgər qarşı tərəf bu bağlantıdadırsa, is_read true olmalıdır
        if event['receiver'] == self.user.username:
            is_read = await self.mark_as_read(event['message_id'])

            # # Yeni: notification göndər
            # await self.send(text_data=json.dumps({
            #     "type": "notification",  # xüsusi tip
            #     "event": "new_message",
            #     "message": event["message"],
            #     "sender": event["sender"],
            #     "timestamp": event["timestamp"],
            # }))

        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "sender": event["sender"],
            "receiver": event["receiver"],
            "timestamp": event["timestamp"],
            "message_id": event["message_id"],
            "is_read": is_read,
        }))

    def get_room_name(self, user1, user2):
        return f"chat_{'_'.join(sorted([user1, user2]))}"

    @database_sync_to_async
    def get_user(self, username):
        return User.objects.get(username=username)

    @database_sync_to_async
    def create_message(self, sender, receiver, message):
        return ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            message=message
        )

    @database_sync_to_async
    def is_blocked(self, sender_username, receiver_username):
        try:
            blocker = User.objects.get(username=receiver_username)
            blocked = User.objects.get(username=sender_username)
            return any([
                BlockedUser.objects.filter(blocker=blocker, blocked=blocked).exists(),
                BlockedUser.objects.filter(blocker=blocked, blocked=blocker).exists(),
            ])
        except User.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_as_read(self, message_id):
        try:
            msg = ChatMessage.objects.get(id=message_id)
            msg.is_read = True
            msg.save()
            return True
        except ChatMessage.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_multiple_as_read(self, ids):
        qs = ChatMessage.objects.filter(id__in=ids, receiver=self.user, is_read=False)
        updated_ids = list(qs.values_list("id", flat=True))
        qs.update(is_read=True)
        return updated_ids
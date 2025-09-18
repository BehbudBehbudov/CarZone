from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import *


#Registrasiya hissesi
class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerificationCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class FinalRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user



#Sifre sifirlama
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])



#Masin ucun lazim olanlar
class CarImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ['id', 'image', 'is_main']


class CarSerializer(serializers.ModelSerializer):
    images = CarImageSerializer(many=True, read_only=True)
    seller = serializers.StringRelatedField()
    category = serializers.SlugRelatedField(
        slug_field='name',
        queryset=Category.objects.all()
    )

    # Seçim siyahılarını frontendə göndərmək üçün
    fuel_types = serializers.SerializerMethodField()
    transmission_types = serializers.SerializerMethodField()
    condition_types = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            'id', 'title', 'description', 'price', 'year', 'mileage',
            'fuel_type', 'transmission', 'condition', 'color', 'engine_size',
            'category', 'seller', 'is_sold', 'created_at', 'images',
            'fuel_types', 'transmission_types', 'condition_types'
        ]
        read_only_fields = ('seller', 'created_at', 'updated_at')

    def get_fuel_types(self, obj):
        return dict(Car.FUEL_TYPES)

    def get_transmission_types(self, obj):
        return dict(Car.TRANSMISSION_TYPES)

    def get_condition_types(self, obj):
        return dict(Car.CONDITION_TYPES)


#Commment
class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at']


#Chat
class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    receiver = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all())
    is_read = serializers.BooleanField(read_only=True)  # əlavə olunur

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'receiver', 'message', 'created_at', 'updated_at', 'is_read']
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at', 'is_read']


#Add to Favorites
class FavoriteCarSerializer(serializers.ModelSerializer):
    car = CarSerializer(read_only=True)

    class Meta:
        model = FavoriteCar
        fields = ['id', 'car', 'created_at']

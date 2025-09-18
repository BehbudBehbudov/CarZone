from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Car(models.Model):
    # Admin tərəfindən əlavə olunacaq seçimlər
    FUEL_TYPES = (
        ('petrol', 'Benzin'),
        ('diesel', 'Dizel'),
        ('electric', 'Elektrik'),
        ('hybrid', 'Hibrid'),
    )

    TRANSMISSION_TYPES = (
        ('manual', 'Mexaniki'),
        ('automatic', 'Avtomat'),
    )

    CONDITION_TYPES = (
        ('new', 'Yeni'),
        ('used', 'İşlənmiş'),
    )

    # Əsas sahələr
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cars')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    number = models.CharField(max_length=20, default='Yoxdur')
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    year = models.PositiveIntegerField()
    mileage = models.PositiveIntegerField()

    # Sabit seçim sahələri
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPES)
    transmission = models.CharField(max_length=10, choices=TRANSMISSION_TYPES)
    condition = models.CharField(max_length=5, choices=CONDITION_TYPES)

    # Əlavə detallar
    color = models.CharField(max_length=50)
    engine_size = models.DecimalField(max_digits=3, decimal_places=1)
    is_sold = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.price}"


class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='car_images/')
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.car.title}"


class Comment(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.car.title}"


class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Mesajı hər iki tərəf üçün silmə/saxlama
    sender_deleted = models.BooleanField(default=False)
    receiver_deleted = models.BooleanField(default=False)



    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.message[:30]}"



class BlockedUser(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blocker', 'blocked')

    def __str__(self):
        return f"{self.blocker.username} blocked {self.blocked.username}"


class FavoriteCar(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_cars')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'car')

    def __str__(self):
        return f"{self.user.username} -> {self.car.title}"

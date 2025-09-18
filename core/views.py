from rest_framework import generics,viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from .serializers import *
from .verify_codes import verification_store
import random
from django.core.mail import send_mail
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from .models import *
from .filters import CarFilter
from django.db.models import Q


class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def send_email(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = str(random.randint(100000, 999999))
        verification_store[email] = code
        print(f"[TEST] Sent code {code} to {email}")
        return Response({'message': 'Verification code sent (check console).'}, status=200)

    @action(detail=False, methods=['post'])
    def verify_code(self, request):
        serializer = VerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        if verification_store.get(email) == code:
            return Response({'message': 'Code verified.'})
        return Response({'error': 'Invalid code'}, status=400)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = FinalRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        if email not in verification_store:
            return Response({'error': 'Email not verified'}, status=400)
        serializer.save()
        verification_store.pop(email, None)
        return Response({'message': 'User registered successfully'})


class LoginViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            # Emailə görə istifadəçini tap
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        # İndi `username` ilə authenticate et
        user = authenticate(username=user_obj.username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'Invalid credentials'}, status=401)


class LogoutViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def logout(self, request):
        return Response({'message': 'Logged out (token discard on client side)'})


# Yaddaşda saxlanılan kodlar və təsdiqlənmiş emaillər
code_store = {}
verified_emails = set()

class PasswordResetViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def request(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'İstifadəçi tapılmadı'}, status=404)

        code = str(random.randint(100000, 999999))
        code_store[email] = code  # sadə yaddaş
        # print(f"[DEBUG] Kod: {code}")

        send_mail(
            subject="Şifrə sıfırlama kodu",
            message=f"Sizin kodunuz: {code}",
            from_email="bbehbudov879@gmail.com",
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({'message': 'Kod e-mailə göndərildi'}, status=200)

    @action(detail=False, methods=['post'])
    def verify(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        if code_store.get(email) == code:
            verified_emails.add(email)
            return Response({'message': 'Kod təsdiqləndi'}, status=200)
        return Response({'error': 'Yanlış kod'}, status=400)

    @action(detail=False, methods=['post'])
    def confirm(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']

        if email not in verified_emails:
            return Response({'error': 'Email təsdiqlənməyib'}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'İstifadəçi tapılmadı'}, status=404)

        user.password = make_password(new_password)
        user.save()

        # Temizleme
        verified_emails.discard(email)
        code_store.pop(email, None)

        return Response({'message': 'Şifrə uğurla dəyişdirildi'}, status=200)


class CarViewSet(viewsets.ModelViewSet):
    serializer_class = CarSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = (JSONParser, MultiPartParser, FormParser)
    filter_backends = [DjangoFilterBackend]
    filterset_class = CarFilter  # filterset_fields əvəzinə filterset_class

    def get_queryset(self):
        queryset = Car.objects.all().order_by('-created_at')

        # Əgər "mənim elanlarım" sorğusudursa
        if self.request.query_params.get('my_cars') == 'true' and self.request.user.is_authenticated:
            queryset = queryset.filter(seller=self.request.user)

        # Əlavə axtarış funksiyası
        search_query = self.request.query_params.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(color__icontains=search_query) |
                Q(seller__username__icontains=search_query)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.seller != request.user:
            return Response(
                {'error': 'Yalnız elan sahibi yeniləyə bilər'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.seller != request.user:
            return Response(
                {'error': 'Yalnız elan sahibi silə bilər'},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['POST'], parser_classes=[MultiPartParser])
    def upload_images(self, request, pk=None):
        car = self.get_object()
        if car.seller != request.user:
            return Response(
                {'error': 'Yalnız elan sahibi şəkil yükləyə bilər'},
                status=status.HTTP_403_FORBIDDEN
            )

        images = request.FILES.getlist('images')
        for image in images:
            CarImage.objects.create(car=car, image=image)

        return Response(
            {'message': f'{len(images)} şəkil uğurla yükləndi'},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['GET'])
    def my_cars(self, request):
        queryset = self.filter_queryset(self.get_queryset().filter(seller=request.user))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    # Əlavə axtarış action-u
    @action(detail=False, methods=['GET'])
    def search(self, request):
        """
        Məhsul axtarışı
        GET /cars/search/?q=bmw&category=1&price_min=5000
        """
        query = request.query_params.get('q', '').strip()

        if not query:
            return Response({'error': 'Axtarış sorğusu boş ola bilməz'}, status=400)

        # Axtarış nəticələri
        queryset = self.get_queryset().filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(color__icontains=query)
        )

        # Filtri tətbiq et
        queryset = self.filter_queryset(queryset)

        # Nəticələr boşdursa
        if not queryset.exists():
            return Response({
                'message': f'"{query}" üçün nəticə tapılmadı',
                'count': 0,
                'results': []
            })

        # Serializer və nəticəni qaytar
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'message': f'"{query}" üçün {queryset.count()} nəticə tapıldı',
            'count': queryset.count(),
            'results': serializer.data
        })


#Comment
class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(car_id=self.kwargs['car_pk']).order_by('-created_at')

    def perform_create(self, serializer):
        car = Car.objects.get(pk=self.kwargs['car_pk'])
        serializer.save(user=self.request.user, car=car)

    # Yalnız komment sahibi yeniləyə bilər
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {'error': 'Yalnız öz kommentinizi yeniləyə bilərsiniz'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    # Yalnız komment sahibi silə bilər
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {'error': 'Yalnız öz kommentinizi silə bilərsiniz'},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


#Chat sistemi
class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        partner_username = self.request.query_params.get('with')

        queryset = ChatMessage.objects.filter(
            models.Q(sender=user, sender_deleted=False) |
            models.Q(receiver=user, receiver_deleted=False)
        )

        if partner_username:
            queryset = queryset.filter(
                models.Q(sender=user, receiver__username=partner_username) |
                models.Q(sender__username=partner_username, receiver=user)
            )

            # Burada oxunmamış mesajları oxunmuş kimi işarələ
            queryset.filter(receiver=user, is_read=False).update(is_read=True)

        return queryset.order_by('created_at')

    def perform_create(self, serializer):
        sender = self.request.user
        receiver = serializer.validated_data['receiver']

        if BlockedUser.objects.filter(blocker=receiver, blocked=sender).exists():
            raise serializers.ValidationError("Bu istifadəçi sizi blok edib, mesaj göndərə bilməzsiniz.")

        serializer.save(sender=sender)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.sender != request.user:
            return Response({'error': 'Yalnız öz mesajını yeniləyə bilərsən'}, status=403)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        # Hər iki tərəf silibsə, həqiqətən sil
        if user == instance.sender:
            instance.sender_deleted = True
        elif user == instance.receiver:
            instance.receiver_deleted = True
        else:
            return Response({'error': 'Bu mesaj sənə aid deyil'}, status=403)

        if instance.sender_deleted and instance.receiver_deleted:
            instance.delete()
        else:
            instance.save()

        return Response({'message': 'Mesaj silindi'}, status=204)


    @action(detail=False, methods=['post'], url_path='block')
    def block_user(self, request):
        username = request.data.get('username')
        if not username:
            return Response({'error': 'İstifadəçi adı tələb olunur'}, status=400)

        try:
            blocked_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'İstifadəçi tapılmadı'}, status=404)

        if request.user == blocked_user:
            return Response({'error': 'Özünü bloklamaq olmaz'}, status=400)

        obj, created = BlockedUser.objects.get_or_create(
            blocker=request.user,
            blocked=blocked_user
        )
        if created:
            return Response({'message': f'{username} bloklandı'}, status=201)
        else:
            return Response({'message': f'{username} artıq bloklanıb'}, status=200)


    @action(detail=False, methods=['post'], url_path='unblock')
    def unblock_user(self, request):
        username = request.data.get('username')
        if not username:
            return Response({'error': 'İstifadəçi adı tələb olunur'}, status=400)

        try:
            blocked_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'İstifadəçi tapılmadı'}, status=404)

        try:
            obj = BlockedUser.objects.get(blocker=request.user, blocked=blocked_user)
            obj.delete()
            return Response({'message': f'{username} blokdan çıxarıldı'}, status=200)
        except BlockedUser.DoesNotExist:
            return Response({'error': f'{username} blokda deyil'}, status=400)


#Filter sistemi
class CarFilterView(generics.ListAPIView):
    queryset = Car.objects.all().order_by('-created_at')
    serializer_class = CarSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CarFilter


#Add to Favorites
class FavoriteCarViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        queryset = FavoriteCar.objects.filter(user=request.user)
        serializer = FavoriteCarSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        car_id = request.data.get('car_id')
        try:
            car = Car.objects.get(id=car_id)
            favorite, created = FavoriteCar.objects.get_or_create(user=request.user, car=car)
            if not created:
                return Response({'message': 'Bu elan artıq bəyənilib'}, status=400)
            return Response({'message': 'Elan bəyənildi'}, status=201)
        except Car.DoesNotExist:
            return Response({'error': 'Maşın tapılmadı'}, status=404)

    @action(detail=False, methods=['delete'])
    def remove(self, request):
        car_id = request.data.get('car_id')
        try:
            favorite = FavoriteCar.objects.get(user=request.user, car_id=car_id)
            favorite.delete()
            return Response({'message': 'Bəyənilənlərdən silindi'})
        except FavoriteCar.DoesNotExist:
            return Response({'error': 'Bu elan bəyənilməmişdi'}, status=404)

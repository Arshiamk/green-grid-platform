from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers

from customers.models import Customer


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "password", "first_name", "last_name", "email", "phone"]
        extra_kwargs = {"phone": {"write_only": True}}

    def create(self, validated_data):
        phone = validated_data.pop("phone", "")
        
        with transaction.atomic():
            # Create User
            user = User.objects.create_user(
                username=validated_data["username"],
                password=validated_data["password"],
                first_name=validated_data["first_name"],
                last_name=validated_data["last_name"],
                email=validated_data["email"],
            )

            # Create Customer linked to User
            # We'll generate a random account number or use a sequence. 
            # For now, let's use 'GG-' + random UUID hex
            import uuid
            account_number = f"GG-{uuid.uuid4().hex[:8].upper()}"
            
            Customer.objects.create(
                user=user,
                account_number=account_number,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone=phone,
            )
            
        return user

from rest_framework import serializers

from .models import Hostel, HostelExpense, HostelRoom


class HostelSerializer(serializers.ModelSerializer):
    room_count = serializers.IntegerField(source="rooms.count", read_only=True)
    resident_count = serializers.IntegerField(source="residents.count", read_only=True)

    class Meta:
        model = Hostel
        fields = (
            "id",
            "name",
            "code",
            "monthly_fee",
            "currency",
            "capacity",
            "warden_name",
            "warden_phone",
            "description",
            "is_active",
            "room_count",
            "resident_count",
        )


class HostelRoomSerializer(serializers.ModelSerializer):
    hostel_code = serializers.CharField(source="hostel.code", read_only=True)

    class Meta:
        model = HostelRoom
        fields = ("id", "hostel", "hostel_code", "room_number", "floor", "capacity", "is_active")


class HostelExpenseSerializer(serializers.ModelSerializer):
    hostel_name = serializers.CharField(source="hostel.name", read_only=True)

    class Meta:
        model = HostelExpense
        fields = (
            "id",
            "hostel",
            "hostel_name",
            "category",
            "amount",
            "currency",
            "spent_on",
            "vendor",
            "payment_method",
            "notes",
        )

from rest_framework import serializers

from .models import TransportExpense, TransportRoute, Vehicle


class TransportRouteSerializer(serializers.ModelSerializer):
    vehicle_count = serializers.IntegerField(source="vehicles.count", read_only=True)
    rider_count = serializers.IntegerField(source="students.count", read_only=True)

    class Meta:
        model = TransportRoute
        fields = (
            "id",
            "name",
            "code",
            "monthly_fare",
            "currency",
            "description",
            "is_active",
            "vehicle_count",
            "rider_count",
        )


class VehicleSerializer(serializers.ModelSerializer):
    route_name = serializers.CharField(source="route.name", read_only=True)

    class Meta:
        model = Vehicle
        fields = (
            "id",
            "registration_number",
            "model",
            "capacity",
            "driver_name",
            "driver_phone",
            "route",
            "route_name",
            "is_active",
        )


class TransportExpenseSerializer(serializers.ModelSerializer):
    vehicle_reg = serializers.CharField(source="vehicle.registration_number", read_only=True)
    route_name = serializers.CharField(source="route.name", read_only=True)

    class Meta:
        model = TransportExpense
        fields = (
            "id",
            "vehicle",
            "vehicle_reg",
            "route",
            "route_name",
            "category",
            "amount",
            "currency",
            "spent_on",
            "vendor",
            "payment_method",
            "notes",
        )

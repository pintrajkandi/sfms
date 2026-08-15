from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenants", "0007_backuprun_client_backuprun_schema_name_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlatformSupportTicket",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("schema_name", models.CharField(db_index=True, max_length=63)),
                ("school_name", models.CharField(blank=True, max_length=200)),
                ("subject", models.CharField(max_length=200)),
                ("category", models.CharField(default="other", max_length=20)),
                ("message", models.TextField()),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("submitted_by", models.CharField(blank=True, max_length=200)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("in_progress", "In Progress"),
                            ("resolved", "Resolved"),
                        ],
                        default="open",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
    ]

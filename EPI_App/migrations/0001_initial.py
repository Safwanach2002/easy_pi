# Generated by Django 5.0.1 on 2025-02-26 00:39

import django.db.models.deletion
import django.utils.timezone
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Combo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=100, null=True)),
                ('title', models.CharField(max_length=50)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('desc', models.CharField(max_length=500, null=True)),
                ('category', models.CharField(choices=[('electronics', 'Electronics'), ('mobiles', 'Mobiles'), ('home_kitchen', 'Home & Kitchen'), ('fashion', 'Fashion'), ('books', 'Books'), ('others', 'Others')], default='others', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Services',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=100, null=True)),
                ('title', models.CharField(max_length=50)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('desc', models.CharField(max_length=500, null=True)),
                ('category', models.CharField(choices=[('electronics', 'Electronics'), ('mobiles', 'Mobiles'), ('home_kitchen', 'Home & Kitchen'), ('fashion', 'Fashion'), ('books', 'Books'), ('others', 'Others')], default='others', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Upto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=100, null=True)),
                ('title', models.CharField(max_length=50)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('desc', models.CharField(max_length=500, null=True)),
                ('category', models.CharField(choices=[('kids', 'Kids'), ('teens', 'Teens'), ('youths', 'Youths'), ('others', 'Others')], default='others', max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='ComboImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='pics')),
                ('Combo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='EPI_App.combo')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('referral_code', models.CharField(blank=True, max_length=8, null=True, unique=True)),
                ('profile_photo', models.ImageField(blank=True, null=True, upload_to='profile_photos/')),
                ('kyc_document', models.FileField(blank=True, null=True, upload_to='kyc_documents/')),
                ('kyc_document_type', models.CharField(blank=True, max_length=50, null=True)),
                ('pan_card', models.FileField(blank=True, null=True, upload_to='pan_cards/')),
                ('bank_passbook', models.FileField(blank=True, null=True, upload_to='bank_passbooks/')),
                ('referrals_made', models.IntegerField(default=0)),
                ('rewards_earned', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10)),
                ('referred_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals', to='EPI_App.profile')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ProductScheme',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=100, null=True)),
                ('investment', models.DecimalField(decimal_places=2, max_digits=10)),
                ('start_date', models.DateField(auto_now_add=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('days', models.IntegerField()),
                ('total', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
                ('profile', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='EPI_App.profile')),
            ],
        ),
        migrations.CreateModel(
            name='PaymentOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=100, unique=True)),
                ('product_id', models.CharField(max_length=100, null=True)),
                ('amount', models.IntegerField()),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('payment_id', models.CharField(blank=True, max_length=100)),
                ('payment_status', models.CharField(choices=[('PENDING', 'Pending'), ('SUCCESSFUL', 'Successful'), ('FAILED', 'Failed')], default='PENDING', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('profile', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='EPI_App.profile')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('payment_proof', models.ImageField(blank=True, null=True, upload_to='payment_proofs/')),
                ('payment_status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('product_scheme', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='EPI_App.productscheme')),
                ('profile', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='EPI_App.profile')),
            ],
        ),
        migrations.CreateModel(
            name='Referral',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('referred_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='referral_by', to='EPI_App.profile')),
                ('referred_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='referred_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ServiceImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='pics')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='EPI_App.services')),
            ],
        ),
        migrations.CreateModel(
            name='Investment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('daily_investment', models.DecimalField(decimal_places=2, max_digits=10)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('days_to_complete', models.IntegerField()),
                ('start_date', models.DateField(auto_now_add=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('referred_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='EPI_App.services')),
            ],
        ),
        migrations.CreateModel(
            name='UptoImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='pics')),
                ('upto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='EPI_App.upto')),
            ],
        ),
        migrations.CreateModel(
            name='WithdrawalRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('tds_deduction', models.DecimalField(decimal_places=2, max_digits=10)),
                ('final_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('method', models.CharField(choices=[('bank', 'Bank Transfer'), ('upi', 'UPI Transfer')], max_length=10)),
                ('account_number', models.CharField(blank=True, max_length=50, null=True)),
                ('upi_id', models.CharField(blank=True, max_length=50, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('success', 'Success')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('combo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='EPI_App.combo')),
                ('service', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='EPI_App.services')),
                ('upto', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='EPI_App.upto')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'service', 'upto', 'combo')},
            },
        ),
    ]

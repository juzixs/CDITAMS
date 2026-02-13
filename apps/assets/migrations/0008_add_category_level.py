from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0007_locationareabinding'),
    ]

    operations = [
        migrations.AddField(
            model_name='assetcategory',
            name='level',
            field=models.IntegerField(choices=[(1, '1级'), (2, '2级'), (3, '3级'), (4, '4级')], default=1, verbose_name='分类级别'),
        ),
    ]

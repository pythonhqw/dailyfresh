# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GoodsCategory',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='修改时间', auto_now=True)),
                ('name', models.CharField(verbose_name='类别名称', max_length=20)),
                ('logo', models.CharField(verbose_name='图标标识', max_length=100)),
                ('image', models.ImageField(verbose_name='类别图片', upload_to='category')),
            ],
            options={
                'verbose_name': '商品类别',
                'db_table': 'df_goods_category',
                'verbose_name_plural': '商品类别',
            },
        ),
        migrations.CreateModel(
            name='GoodsImage',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='修改时间', auto_now=True)),
                ('image', models.ImageField(verbose_name='图片', upload_to='goods')),
            ],
            options={
                'verbose_name': '商品图片',
                'db_table': 'df_goods_image',
                'verbose_name_plural': '商品图片',
            },
        ),
        migrations.CreateModel(
            name='GoodsSKU',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='修改时间', auto_now=True)),
                ('name', models.CharField(verbose_name='名称', max_length=100)),
                ('title', models.CharField(verbose_name='简介', max_length=200)),
                ('unit', models.CharField(verbose_name='销售单位', max_length=10)),
                ('price', models.DecimalField(verbose_name='价格', decimal_places=2, max_digits=10)),
                ('stock', models.IntegerField(verbose_name='库存', default=0)),
                ('sales', models.IntegerField(verbose_name='销量', default=0)),
                ('default_image', models.ImageField(verbose_name='图片', upload_to='goods')),
                ('status', models.BooleanField(verbose_name='是否上线', default=True)),
                ('category', models.ForeignKey(verbose_name='类别', to='goods.GoodsCategory')),
            ],
            options={
                'verbose_name': '商品SKU',
                'db_table': 'df_goods_sku',
                'verbose_name_plural': '商品SKU',
            },
        ),
        migrations.CreateModel(
            name='GoodsSPU',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='修改时间', auto_now=True)),
                ('name', models.CharField(verbose_name='名称', max_length=100)),
                ('desc', tinymce.models.HTMLField(verbose_name='商品描述', blank=True, default='')),
            ],
            options={
                'verbose_name': '商品',
                'db_table': 'df_goods_spu',
                'verbose_name_plural': '商品',
            },
        ),
        migrations.CreateModel(
            name='IndexCategoryGoods',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='修改时间', auto_now=True)),
                ('display_type', models.SmallIntegerField(verbose_name='展示类型', choices=[(0, '标题'), (1, '图片')])),
                ('index', models.SmallIntegerField(verbose_name='顺序', default=0)),
                ('category', models.ForeignKey(verbose_name='商品类别', to='goods.GoodsCategory')),
                ('sku', models.ForeignKey(verbose_name='商品SKU', to='goods.GoodsSKU')),
            ],
            options={
                'verbose_name': '主页分类展示商品',
                'db_table': 'df_index_category_goods',
                'verbose_name_plural': '主页分类展示商品',
            },
        ),
        migrations.CreateModel(
            name='IndexPromotion',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='修改时间', auto_now=True)),
                ('name', models.CharField(verbose_name='活动名称', max_length=50)),
                ('url', models.CharField(verbose_name='活动连接', max_length=100)),
                ('image', models.ImageField(verbose_name='图片', upload_to='banner')),
                ('index', models.SmallIntegerField(verbose_name='顺序', default=0)),
            ],
            options={
                'verbose_name': '主页促销活动',
                'db_table': 'df_index_promotion',
                'verbose_name_plural': '主页促销活动',
            },
        ),
        migrations.CreateModel(
            name='IndexSlideGoods',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('create_time', models.DateTimeField(verbose_name='创建时间', auto_now_add=True)),
                ('update_time', models.DateTimeField(verbose_name='修改时间', auto_now=True)),
                ('image', models.ImageField(verbose_name='图片', upload_to='banner')),
                ('index', models.SmallIntegerField(verbose_name='顺序', default=0)),
                ('sku', models.ForeignKey(verbose_name='商品SKU', to='goods.GoodsSKU')),
            ],
            options={
                'verbose_name': '主页轮播商品',
                'db_table': 'df_index_slide_goods',
                'verbose_name_plural': '主页轮播商品',
            },
        ),
        migrations.AddField(
            model_name='goodssku',
            name='spu',
            field=models.ForeignKey(verbose_name='商品SPU', to='goods.GoodsSPU'),
        ),
        migrations.AddField(
            model_name='goodsimage',
            name='sku',
            field=models.ForeignKey(verbose_name='商品SKU', to='goods.GoodsSKU'),
        ),
    ]

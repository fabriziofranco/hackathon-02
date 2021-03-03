from admin_numeric_filter.forms import RangeNumericForm, SliderNumericForm
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from admin_numeric_filter.admin import NumericFilterModelAdmin, SingleNumericFilter, RangeNumericFilter, \
    SliderNumericFilter

from agricultores.models import *



class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('phone_number',)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('phone_number',
                  'email',
                  'first_name',
                  'last_name',
                  'profile_picture_URL',
                  'number_of_credits',
                  'RUC',
                  'DNI',
                  'latitude',
                  'longitude',
                  'district',
                  'is_advertiser',
                  'role',
                  'password',
                  'is_active',
                  'is_admin'
                  )

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = UserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ('phone_number', 'first_name', 'last_name', 'email', 'role', 'district', 'is_admin')
    list_filter = ('is_admin', 'role')
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {'fields': ('email',
                                      'first_name',
                                      'last_name',
                                      'profile_picture_URL',
                                      'number_of_credits',
                                      'district',
                                      'RUC',
                                      'DNI',
                                      'role'
                                      )
                           }
         ),
        ('Coordenadas', {'fields': ('latitude', 'longitude')}
         ),
        ('Permissions', {'fields': ('is_admin', 'is_advertiser',)}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'email', 'password1', 'password2'),
        }),
    )
    search_fields = ('phone_number', 'email', 'first_name', 'last_name')
    ordering = ('phone_number',)
    filter_horizontal = ()


class SupplyAdmin(admin.ModelAdmin):
    list_display = ('name', 'count_cultivos_vendidos','count_cultivos_sin_vender',
                    'count_pedidos_vendidos','count_pedidos_sin_vender',)
    search_fields = ('name',)
    ordering = ('name',)



    def count_cultivos_vendidos(self, obj):
        from django.db.models import Count
        result = Publish.objects.filter(supplies=obj, is_sold=True).aggregate(Count("supplies"))
        return result["supplies__count"]

    count_cultivos_vendidos.short_description = "Nº Cultivos vendidos"

    def count_cultivos_sin_vender(self, obj):
        from django.db.models import Count
        result = Publish.objects.filter(supplies=obj, is_sold=False).aggregate(Count("supplies"))
        return result["supplies__count"]

    count_cultivos_sin_vender.short_description = "Nº Cultivos sin vender"


    def count_pedidos_vendidos(self, obj):
        from django.db.models import Count
        result = Order.objects.filter(supplies=obj, is_solved=True).aggregate(Count("supplies"))
        return result["supplies__count"]

    count_pedidos_vendidos.short_description = "Nº Pedidos vendidos"

    def count_pedidos_sin_vender(self, obj):
        from django.db.models import Count
        result = Order.objects.filter(supplies=obj, is_solved=False).aggregate(Count("supplies"))
        return result["supplies__count"]

    count_pedidos_sin_vender.short_description = "Nº Pedidos sin vender"

    #count_pedidos_sin_vender.admin_order_field = 'count_pedidos_sin_vender'




admin.site.site_header = "Panel Administrativo - COSECHA"


class PublishAdmin(admin.ModelAdmin):
    list_display = ('user', 'supplies', 'unit_price', 'weight_unit', 'harvest_date',
                    'is_sold', "test")

    list_filter = (('unit_price', SliderNumericFilter), 'is_sold', 'supplies',
                   )

    def test(self, obj):
        return obj.user.district

    test.short_description = 'DISTRICT'
    test.admin_order_field = 'user__district'


class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'supplies', 'unit_price', 'weight_unit', 'desired_harvest_date',
                    'is_solved', "test")

    list_filter = (('unit_price', SliderNumericFilter), 'is_solved', 'supplies',
                   )

    def test(self, obj):
        return obj.user.district

    test.short_description = 'DISTRICT'
    test.admin_order_field = 'user__district'


# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Supply, SupplyAdmin)
admin.site.register(Publish, PublishAdmin)
admin.site.register(Order, OrderAdmin)
# admin.site.register(Advertisement)
# admin.site.register(AddressedTo)

# admin.site.register(Department)
# admin.site.register(Region)
# admin.site.register(District)

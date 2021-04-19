from django.db.models import Count

from admin_numeric_filter.forms import RangeNumericForm, SliderNumericForm
from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from admin_numeric_filter.admin import *
from django.db.models import When, F, Q

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


class SupplyCreationForm(forms.ModelForm):
    class Meta:
        model = Supply
        fields = ('name', 'days_for_harvest')


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
                  'number_of_credits',
                  'profile_picture_URL',
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


class SupplyForm(forms.ModelForm):
    class Meta:
        model = Supply
        fields = ('name',
                  'days_for_harvest'
                  )


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
                                      'district',
                                      'RUC',
                                      'DNI',
                                      'role'
                                      )
                           }
         ),
        ('Créditos', {'fields': ('number_of_credits',)}
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


class SupplyAdmin(NumericFilterModelAdmin):
    list_display = (
        'name', 'sold_count', 'unsold_count', 'solved_count', 'unsolved_count')

    search_fields = ('name',)
    ordering = ('name',)

    def get_queryset(self, request):
        sold_pubs = Count('publish', filter=Q(publish__is_sold=True),  distinct=True)
        unsold_pubs = Count('publish', filter=Q(publish__is_sold=False),  distinct=True)
        solved_orders = Count('order', filter=Q(order__is_solved=True),  distinct=True)
        unsolved_orders = Count('order', filter=Q(order__is_solved=False),  distinct=True)

        sup=Supply.objects.annotate(sold_count=sold_pubs).\
            annotate(unsold_count=unsold_pubs).\
            annotate(solved_count=solved_orders).\
            annotate(unsolved_count=unsolved_orders)
        print(sup)
        return sup

    def sold_count(self, obj):
        return obj.sold_count

    sold_count.admin_order_field = 'sold_count'
    sold_count.short_description = 'Sold publications'

    def unsold_count(self, obj):
        return obj.unsold_count

    unsold_count.admin_order_field = 'unsold_count'
    unsold_count.short_description = 'Unsold publications'

    def solved_count(self, obj):
        return obj.solved_count

    solved_count.admin_order_field = 'solved_count'
    solved_count.short_description = 'Solved orders'

    def unsolved_count(self, obj):
        return obj.unsolved_count

    unsolved_count.admin_order_field = 'unsolved_count'
    unsolved_count.short_description = 'Unsolved orders'

    list_filter = SolvedOrdersFilter, UnsolvedOrdersFilter, SoldPublicationFilter, UnsoldPublicationFilter

    change_form = SupplyForm
    add_form = SupplyCreationForm

    def get_form(self, request, obj=None, **kwargs):
        if not obj:
            self.form = self.add_form
        else:
            self.form = self.change_form

        return super(SupplyAdmin, self).get_form(request, obj, **kwargs)


admin.site.site_header = "Panel Administrativo - COSECHA"


class PublishAdmin(NumericFilterModelAdmin):
    list_display = ('user', 'supplies', 'unit_price', 'weight_unit', 'harvest_date',
                    'is_sold', "test")

    list_filter = (('unit_price', RangeNumericFilter), 'is_sold')

    def test(self, obj):
        return obj.user.district

    test.short_description = 'DISTRICT'
    test.admin_order_field = 'user__district'
    ordering = ('is_sold', 'supplies')

    search_fields = ('user__district__name', 'user__district__region__name', 'user__district__department__name',
                     'supplies__name')


class OrderAdmin(NumericFilterModelAdmin):
    list_display = ('user', 'supplies', 'unit_price', 'weight_unit', 'desired_harvest_date',
                    'is_solved', "test")

    list_filter = (('unit_price', RangeNumericFilter), 'is_solved')

    def test(self, obj):
        return obj.user.district

    test.short_description = 'DISTRICT'
    test.admin_order_field = 'user__district'
    search_fields = (
        'user__district__name', 'user__district__region__name', 'user__district__department__name', 'supplies__name')
    ordering = ('is_solved', 'supplies')


class AdAdmin(NumericFilterModelAdmin):
    list_display = ('user', 'name', 'original_credits', 'remaining_credits', 'department', 'region',
                    'test', "for_publications", "for_orders")

    list_filter = (('original_credits', RangeNumericFilter), ('remaining_credits', RangeNumericFilter), 'for_orders',
                   'for_publications')

    def test(self, obj):
        if obj.district:
            return obj.district.name
        else:
            return '-'

    test.short_description = 'DISTRICT'
    test.admin_order_field = 'district__name'
    ordering = ('name', 'user')

    search_fields = ('name', 'user__phone_number', 'district__name', 'region__name',
                     'department__name')


class LinkedToAdmin(admin.ModelAdmin):
    list_display = ('advertisement', 'supply')

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.id > 1:
            return False
        return super().has_change_permission(request, obj=obj)

    ordering = ('advertisement', 'supply')

    search_fields = (
        'advertisement__name', 'supply__name', 'advertisement__user__phone_number', 'advertisement__district__name',
        'advertisement__region__name', 'advertisement__department__name')


# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Supply, SupplyAdmin)
admin.site.register(Publish, PublishAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Advertisement, AdAdmin)
admin.site.register(LinkedTo, LinkedToAdmin)

# admin.site.register(Department)
# admin.site.register(Region)
# admin.site.register(Distreict)

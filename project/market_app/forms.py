from django import forms
from .currencies import currencies, exchange_to, DEFAULT_CURRENCY
from .models import Product, Market, ProductType

CURRENCY_CHOICES = [(currency.code, currency.sym) for currency in currencies.values()]


class ProductUpdateForm(forms.ModelForm):
    currency_code = forms.ChoiceField(choices=CURRENCY_CHOICES, initial=DEFAULT_CURRENCY)
    field_order = ['name', 'description', 'currency_code', 'original_price']

    class Meta:
        model = Product
        exclude = ['market', 'created_at']

    def clean_original_price(self):
        return exchange_to(
            DEFAULT_CURRENCY,
            amount=self.data['original_price'],
            _from=self.data['currency_code']
        )


class ProductForm(forms.ModelForm):
    currency_code = forms.ChoiceField(choices=CURRENCY_CHOICES, initial=DEFAULT_CURRENCY)
    field_order = ['name', 'description', 'currency_code', 'original_price']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['market'].queryset = self.user.market_set.all()
        self.initial['market'] = self.user.market_set.first()

    class Meta:
        model = Product
        fields = '__all__'

    def clean_original_price(self):
        return exchange_to(
            DEFAULT_CURRENCY,
            amount=self.data['original_price'],
            _from=self.data['currency_code']
        )


class MarketForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        super(MarketForm, self).__init__(*args, **kwargs)
        self.instance.owner = self.owner

    class Meta:
        model = Market
        exclude = ['owner']


class ProductTypeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product')
        if 'product_type' in kwargs:
            self.product_type = kwargs.pop('product_type')
        super(ProductTypeForm, self).__init__(*args, **kwargs)
        self.instance.product = self.product
        for attr in self.product.get_attributes:
            if attr:
                self.fields[attr] = forms.CharField(
                    label=attr,
                    max_length=63,
                    required=False
                )
                if hasattr(self, 'product_type'):
                    self.fields[attr].initial = self.product_type.properties.get(attr, '')

    def save(self, commit=True):
        properties = {}
        for attr in self.product.get_attributes:
            if attr:
                properties[attr] = self.cleaned_data[attr]
        self.instance.properties = properties
        super(ProductTypeForm, self).save(commit)

    class Meta:
        model = ProductType
        exclude = ['product', 'properties']


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=0, max_value=10)
    product_type = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        self.types = kwargs.pop('types').only('pk')
        super(AddToCartForm, self).__init__(*args, **kwargs)
        self.fields['product_type'].queryset = self.types


class CreditCardForm(forms.Form):
    name_on_card = forms.CharField(max_length=63)
    card_number = forms.IntegerField(
        min_value=1000_0000_0000_0000,
        max_value=9999_9999_9999_9999
    )
    top_up_amount = forms.IntegerField(min_value=1, max_value=1000000)
    currency_code = forms.ChoiceField(choices=CURRENCY_CHOICES)

    def clean_top_up_amount(self):
        return exchange_to(
            DEFAULT_CURRENCY,
            amount=self.data['top_up_amount'],
            _from=self.data['currency_code']
        )


class CheckOutForm(forms.Form):
    agreement = forms.BooleanField(label='Do you agree?', required=False)


class SelectCouponForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.shopping_account = kwargs.pop('shopping_account')
        self.coupons = self.shopping_account.coupon_set
        super(SelectCouponForm, self).__init__(*args, **kwargs)
        self.fields['activated_coupon'] = forms.ModelChoiceField(
            label='Select a coupon',
            initial=self.shopping_account.activated_coupon,
            queryset=self.coupons,
            required=False,
            widget=forms.Select(
                attrs={'onchange': "document.forms.select_coupon.submit();", 'style': 'white-space: normal'}),
        )

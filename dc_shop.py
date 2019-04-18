from dataclasses import asdict, dataclass, is_dataclass, field, fields, MISSING, replace
from decimal import Decimal
from json import JSONEncoder, loads
from typing import List


class DecimalAwareJSONEncoder(JSONEncoder):

    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)

dumps = DecimalAwareJSONEncoder().encode

class JsonEncodable:

    def as_dict(self):
        return asdict(self)

    def as_json(self):
        return dumps(self.as_dict())

    @classmethod
    def from_json(cls, json_str):
        return cls.from_dict(loads(json_str))

    @classmethod
    def _constructor_from_field_type(cls, field_type):
        if issubclass(field_type, JsonEncodable):
            return field_type.from_dict
        elif is_dataclass(field_type):
            return lambda data: field_type(**data)
        else:
            return field_type

    @classmethod
    def from_dict(cls, dict_data):
        data = {}
        for field in fields(cls):
            datum = dict_data.get(field.name)
            if datum:
                if issubclass(field.type, List):
                    sub_type = field.type.__args__[0]
                    constructor = cls._constructor_from_field_type(sub_type)
                    data[field.name] = [constructor(sub_data) for sub_data in datum]
                else:
                    constructor = cls._constructor_from_field_type(field.type)
                    data[field.name] = constructor(datum)
            elif field.default_factory is not MISSING:
                data[field.name] = field.default_factory()
            elif field.default is not MISSING:
                data[field.name] = field.default
        return cls(**data)

@dataclass
class Currency(JsonEncodable):
    name: str
    code: str
    symbol: str
    quant: Decimal = Decimal("0.01")

    def format(self, price):
        return "{} {}".format(price.quantize(self.quant), self.symbol)

@dataclass
class User(JsonEncodable):
    name: str
    perms: List[str] = field(default_factory=list)
    id: int = 0


class TaxType(str):

    SALES_TAX = 'sales_tax'
    VAT = 'vat'

    ALLOWED_VALUES = (SALES_TAX, VAT)

    def __init__(self, value):
        if value not in self.ALLOWED_VALUES:
            raise ValueError("Invalid value")

@dataclass
class Tax(JsonEncodable):
    type: TaxType
    rate: Decimal = Decimal('0.00')

@dataclass
class CartItem(JsonEncodable):
    article: str
    price: Decimal = Decimal('0.00')
    tax: Tax = None
    id: int = 0

    @property
    def calculated_tax(self):
        if self.tax:
            return self.price * self.tax.rate

@dataclass
class Cart(JsonEncodable):
    currency: Currency
    items: List[CartItem] = field(default_factory=list)
    id: int = 0
    user: User = None

    def add(self, item):
        self.items.append(item)

    @property
    def total(self):
        return sum((item.price for item in self.items), Decimal("0.0"))

    @property
    def formatted_total(self):
        return self.currency.format(self.total)

    @property
    def tax(self):
        return sum((item.calculated_tax for item in self.items), Decimal("0.0"))

    @property
    def formatted_tax(self):
        return self.currency.format(self.tax)


if __name__ == "__main__":
    user = User(name="Paul")
    currency = Currency(name="Euro", code="EUR", symbol="€")
    cart = Cart(currency=currency, user=user)
    tax = Tax(type="vat", rate=Decimal("0.13"))
    cart.add(CartItem(article="Box", price=Decimal("100.00"), tax=tax))

    print(Cart.from_json(cart.as_json()))
    print(cart.formatted_total)
    print(cart.formatted_tax)
    assert Cart.from_json(cart.as_json()) == cart

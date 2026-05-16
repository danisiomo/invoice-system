from decimal import Decimal, ROUND_HALF_UP
from app.models.invoice import Invoice

QTY_Q = Decimal("0.0000")
MONEY_Q = Decimal("0.01")
HUNDRED = Decimal("100")

def _q_money(x: Decimal) -> Decimal:
    return x.quantize(MONEY_Q, rounding=ROUND_HALF_UP)

def recalc_invoice_amounts(invoice: Invoice) -> None:
    """
    Пересчёт сумм с/ф
    - если quantity и price заполнены - total_amount = quantity * price
    - vat_amount = total_amount * vat_rate / 100
    - total_with_vat = total_amount + vat_amount
    """
    # сумма без НДС
    base = invoice.total_amount
    if invoice.quantity is not None and invoice.price is not None:
        # quantity может быть с 4 знаками, price с 2
        qty = Decimal(invoice.quantity)
        price = Decimal(invoice.price)
        base = qty * price
        invoice.total_amount = _q_money(base)
    else:
        base = Decimal(invoice.total_amount or 0)
    # Ставка НДС
    rate = Decimal(invoice.vat_rate or 0)
    vat = base * rate / HUNDRED
    invoice.vat_amount = _q_money(vat)
    invoice.total_with_vat = _q_money(base + invoice.vat_amount)
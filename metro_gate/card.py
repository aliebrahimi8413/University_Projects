# کلاس کارت مترو - همون کارتی که مسافر برای رد شدن از گیت لمسش می‌کنه

class Card:
    def __init__(self, card_id, balance=50000):
        self.card_id = card_id
        self.balance = balance   # موجودی کارت (تومان فرض می‌کنیم)

    def has_enough_money(self, fare):
        return self.balance >= fare

    def pay(self, fare):
        # فرض می‌کنیم قبلش چک کردیم که پول کافیه
        self.balance -= fare

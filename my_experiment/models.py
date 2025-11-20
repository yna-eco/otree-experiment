# my_experiment/models.py
from otree.api import *
import random

doc = """
卒論プロトタイプ用モデル（役割固定・5ラウンド・先着順実装）
"""

class Constants(BaseConstants):
    name_in_url = 'my_experiment'
    players_per_group = 5
    num_rounds = 5
    initial_item_count = 2

class Subsession(BaseSubsession):
    condition = models.IntegerField()

    def creating_session(self):
        # condition をラウンド番号で設定
        self.condition = self.round_number

        # ラウンド1のときに役割とrankを初期割当（固定にするため）
        if self.round_number == 1:
            for g in self.get_groups():
                g.item_count = Constants.initial_item_count
                players = g.get_players()
                # 役割割当（任意に変更可）
                for p in players:
                    if p.id_in_group == 1:
                        p.role = 'fan'
                    elif p.id_in_group in [2, 3]:
                        p.role = 'consumer'
                    else:
                        p.role = 'reseller'
                # 順位をランダムに割り振る（先着順用）
                shuffled = players.copy()
                random.shuffle(shuffled)
                for i, p in enumerate(shuffled, start=1):
                    p.rank_in_group = i

class Group(BaseGroup):
    item_count = models.IntegerField(initial=Constants.initial_item_count)
    resale_price = models.CurrencyField(blank=True)
    resale_buyer_id = models.IntegerField(blank=True)
    resale_seller_id = models.IntegerField(blank=True)

class Player(BasePlayer):
    # role: 'consumer', 'reseller', 'fan'
    role = models.StringField()

    # rank (先着順)
    rank_in_group = models.IntegerField(initial=0)

    # --- 主市場（一次市場） ---
    purchase = models.BooleanField(initial=False, blank=True)   # 購入意思（通常販売用）
    quantity = models.IntegerField(initial=0, blank=True)       # 実験1用：何個買うか（0/1/2）
    participate = models.BooleanField(initial=False, blank=True) # オークション参加可否（実験3/5）
    bid_price = models.CurrencyField(blank=True)                # オークション入札価格

    # whether got item in primary market
    primary_bought = models.BooleanField(initial=False)

    # --- 二次市場（簡易） ---
    resale_offer = models.CurrencyField(blank=True)  # 転売: 売りたい値
    resale_bid = models.CurrencyField(blank=True)    # 消費者: 買いたい値

    # 解析用メモ
    note = models.LongStringField(blank=True)

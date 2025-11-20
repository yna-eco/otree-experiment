# my_experiment/pages.py
from otree.api import *
from . import models
from .models import Constants

class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1

    def vars_for_template(self):
        return {'rounds': Constants.num_rounds}

# --- 一次市場: 通常購入（実験1,2,4） ---
class BuyDecisionPage(Page):
    form_model = 'player'

    @property
    def form_fields(self):
        if self.subsession.condition == 1:
            return ['purchase', 'quantity']
        else:
            return ['purchase']

    def is_displayed(self):
        return self.subsession.condition in [1, 2, 4]

# WaitPage: ここで先着順の割当（在庫処理）を一括で行う
class ProcessBuy(WaitPage):
    wait_for_all_groups = False

    def after_all_players_arrive(self):
        g = self.group
        subsession = self.subsession
        # only process for 1,2,4
        if subsession.condition not in [1,2,4]:
            return

        # update item_count per group if not already set for this round
        # Sort players by rank_in_group and allocate
        sorted_players = sorted(g.get_players(), key=lambda p: p.rank_in_group)
        for p in sorted_players:
            p.primary_bought = False  # clear previous flags
            p.quantity = 0

        for p in sorted_players:
            if g.item_count <= 0:
                break
            # If player indicated purchase
            if p.purchase:
                if subsession.condition == 1:
                    desired = int(p.quantity) if p.quantity else 1
                else:
                    desired = 1
                # cap by remaining stock
                allocated = min(desired, g.item_count)
                if allocated > 0:
                    p.quantity = allocated
                    p.primary_bought = True
                    g.item_count -= allocated
                else:
                    p.quantity = 0
            else:
                p.quantity = 0
            p.save()
        g.save()

# --- オークション入力ページ（実験3,5） ---
class AuctionDecisionPage(Page):
    form_model = 'player'
    form_fields = ['participate', 'bid_price']

    def is_displayed(self):
        return self.subsession.condition in [3, 5]

    def before_next_page(self):
        # 単純化: オークションの決着はここでは行わず、後でまとめて行う（TODO）
        pass

# --- 二次市場ページ（簡易マッチング） ---
class ResaleMarketPage(Page):
    form_model = 'player'

    def is_displayed(self):
        # show to resellers who bought in primary, and to consumers/fans who did NOT buy
        if self.player.role == 'reseller':
            return self.player.primary_bought
        elif self.player.role in ['consumer', 'fan']:
            return (not self.player.primary_bought)
        return False

    def get_form_fields(self):
        if self.player.role == 'reseller':
            return ['resale_offer']
        elif self.player.role in ['consumer', 'fan']:
            return ['resale_bid']
        else:
            return []

    def before_next_page(self):
        # マッチングロジックはここでは行わず、簡易的に処理（TODOで改良可能）
        pass

# --- 結果ページ ---
class Results(Page):
    def vars_for_template(self):
        return {
            'role': self.player.role,
            'purchase': self.player.purchase,
            'quantity': self.player.quantity,
            'bid_price': self.player.bid_price,
            'primary_bought': self.player.primary_bought,
            'resale_offer': self.player.resale_offer,
            'resale_bid': self.player.resale_bid,
            'rank': self.player.rank_in_group,
            'remaining_stock': self.group.item_count,
        }

page_sequence = [
    Introduction,
    BuyDecisionPage,
    ProcessBuy,
    AuctionDecisionPage,
    ResaleMarketPage,
    Results
]

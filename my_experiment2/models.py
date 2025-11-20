from otree.api import *
import random


class C(BaseConstants):
    NAME_IN_URL = "my_experiment2"
    PLAYERS_PER_GROUP = 5
    NUM_ROUNDS = 5

    INITIAL_STOCK = 2
    PRIMARY_PRICE = cu(1000)

    # 役割（最初のラウンドでランダム割り当て）
    ROLES = ["consumer", "consumer", "fan", "reseller", "reseller"]

    # ★ 追加：留保価格の候補集合
    CONSUMER_VALUES = [1200, 1200, 1200, 1400, 1400, 1600, 1600, 1900]
    FAN_VALUES = [2000, 2300, 3000]


class Subsession(BaseSubsession):
    # 実験番号（= ラウンド番号）を保存
    condition = models.IntegerField()


class Group(BaseGroup):
    # 一次市場の残り在庫
    remaining_stock = models.IntegerField(initial=0)

    # ▼ 追加：二次市場サマリ
    secondary_buyers_count = models.IntegerField(initial=0)          # 買い手人数
    secondary_items_for_sale = models.IntegerField(initial=0)        # 出品個数
    secondary_trades_count = models.IntegerField(initial=0)          # 成立件数
    secondary_total_trade_value = models.CurrencyField(initial=cu(0))  # 取引総額

class Player(BasePlayer):

    consent = models.BooleanField(
        label="上記の内容に同意し、実験に協力します",
        widget=widgets.CheckboxInput,
    )

    student_id = models.StringField(
        label="学籍番号を入力してください",
        blank=False,   # ← 必須
    )

    scenario_read = models.BooleanField(
        label="上記の内容を読み、理解しました",
        widget=widgets.CheckboxInput,
    )

    role_read = models.BooleanField(
        label="上記の内容を読み、理解しました",
        widget=widgets.CheckboxInput,
    )

    # -------- 基本属性 --------
    p_role = models.StringField()
    reservation_price = models.CurrencyField(blank=True, null=True)

    # -------- 一次市場 --------
    buy_primary = models.IntegerField(
        label="選択してください",
        initial=0,
        choices=[[1, "1点購入したい"], [2, "2点購入したい"], [0, "購入しない"]],
        widget=widgets.RadioSelect,
    )


    bid_primary = models.CurrencyField(
        label="オークション入札額（オークションに参加する場合のみ回答）",
        blank=True,
        null=True,
    )

    # 一次市場の結果
    units_bought_primary = models.IntegerField(initial=0)
    primary_bought = models.BooleanField(initial=False)
    primary_paid = models.CurrencyField(initial=cu(0))

    # -------- 二次市場 --------
    buy_secondary = models.BooleanField(
        label="選択してください",
        blank=True,
        null=True,
        choices=[[True, "二次市場での購入を希望する"], [False, "二次市場では購入しない"]],
        widget=widgets.RadioSelect,
    )

    secondary_price = models.CurrencyField(
        label="あなたが提示する買値（最大この金額なら買いたい価格）※購入を希望する場合のみ回答",
        blank=True,
        null=True,
    )

    resale_price = models.CurrencyField(
        label="あなたが提示する売値（この金額なら売りたい価格）",
        blank=True,
        null=True,
    )

    # ★ 2点目用
    resale_price_2 = models.CurrencyField(
        label="あなたが提示する売値（この金額なら売りたい価格）※2点目がある場合のみ回答",
        blank=True,
        null=True,
    )

    # 二次市場の結果（まだロジックは未実装でもOK）
    units_bought_secondary = models.IntegerField(initial=0)
    units_sold_secondary = models.IntegerField(initial=0)

    # ★ NEW：二次市場で実際に支払った金額（買い手用）
    secondary_spent = models.CurrencyField(initial=cu(0))

    # ★ NEW：二次市場で実際に受け取った金額（売り手用）
    secondary_earned = models.CurrencyField(initial=cu(0))

    # 最終利得（必要に応じて計算用）
    final_payoff = models.CurrencyField(initial=cu(0))


# ===============================================================
#   creating_session   （ラウンド開始時に呼ばれる）
# ===============================================================

def creating_session(subsession: Subsession):
    """
    condition = ラウンド番号（実験番号の意味で使用）
    1: 通常販売
    2: 個数制限
    3: オークション
    4: ファン先行＋通常販売
    5: ファン先行＋オークション
    """

    # 実験番号としてラウンド番号を使用
    subsession.condition = subsession.round_number

    # 在庫は毎ラウンド初期値に戻す
    for g in subsession.get_groups():
        g.remaining_stock = C.INITIAL_STOCK

    if subsession.round_number == 1:
        for g in subsession.get_groups():
            players = g.get_players()
            roles = C.ROLES.copy()
            random.shuffle(roles)
            for p, r in zip(players, roles):
                # 役割を設定
                p.p_role = r
                p.participant.vars["fixed_role"] = r

                # consumer/fan の場合のみ留保価格を設定して固定
                if r == 'consumer':
                    price = random.choice(C.CONSUMER_VALUES)
                    p.reservation_price = price
                    p.participant.vars["fixed_reservation_price"] = price
                elif r == 'fan':
                    price = random.choice(C.FAN_VALUES)
                    p.reservation_price = price
                    p.participant.vars["fixed_reservation_price"] = price
                else:
                    p.reservation_price = None
                    p.participant.vars["fixed_reservation_price"] = None
    else:
        for p in subsession.get_players():
            # ラウンド1で決めた役割を保持
            p.p_role = p.participant.vars.get("fixed_role", "consumer")
            # ラウンド1で決めた留保価格を保持
            p.reservation_price = p.participant.vars.get("fixed_reservation_price", None)



# ===============================================================
#   set_primary_allocation   （一次市場の配分処理）
# ===============================================================

def set_primary_allocation(group: Group):
    """
    実験 1〜5 の一次市場ロジック。

    ・実験1：通常販売（複数可）
    ・実験2：個数制限（1点まで、定価）
    ・実験3：オークション（k+1番目の均一価格）
    ・実験4：ファン先行（定価）＋通常販売
    ・実験5：ファン先行（定価）＋オークション（k+1）
    """

    cond = group.subsession.condition
    players = group.get_players()

    stock = C.INITIAL_STOCK
    group.remaining_stock = stock

    # 初期リセット
    for p in players:
        p.units_bought_primary = 0
        p.primary_bought = False
        p.primary_paid = cu(0)

    # -----------------------------------------------------------
    # 1. ファン先行（実験 4・5）
    # -----------------------------------------------------------
    if cond in [4, 5]:
        fans = [p for p in players if p.p_role == "fan" and p.buy_primary != 0]

        for fan in fans:
            if stock <= 0:
                break

            desired = min(fan.buy_primary, 1, stock)
            fan.units_bought_primary = desired
            fan.primary_bought = True

            # ★ 重要：実験5でも fan の価格は 1000円固定
            fan.primary_paid = C.PRIMARY_PRICE * desired

            stock -= desired

    # -----------------------------------------------------------
    # 2. 一般参加者の候補抽出
    # -----------------------------------------------------------
    if cond in [4, 5]:
        # ファン以外
        candidates = [
            p for p in players
            if p.p_role != "fan" and p.buy_primary != 0
        ]
    else:
        candidates = [p for p in players if p.buy_primary != 0]

    # -----------------------------------------------------------
    # 3-A. オークション方式（実験 3・5）
    # -----------------------------------------------------------
    if cond in [3, 5]:

        if stock > 0:

            # 入札者だけ対象
            bidders = [p for p in candidates if p.bid_primary is not None]

            # 入札者が1人もいない → 誰も買えない
            if not bidders:
                group.remaining_stock = stock
                return

            # 同額のときのランダム性確保
            random.shuffle(bidders)
            bidders.sort(key=lambda pl: pl.bid_primary, reverse=True)

            k = min(stock, len(bidders))  # 落札者数（最大 stock）

            # 上位 k 人が当選
            winners = bidders[:k]
            bids_sorted = [pl.bid_primary for pl in bidders]

            # ★ 均一価格：k+1番目の入札額（存在しなければ k番目）
            if len(bids_sorted) >= k + 1:
                clearing_price = bids_sorted[k]
            else:
                clearing_price = bids_sorted[k - 1]

            # 落札者に1点ずつ配分（価格は均一）
            for w in winners:
                w.units_bought_primary = 1
                w.primary_bought = True
                w.primary_paid = clearing_price

            stock -= k

    # -----------------------------------------------------------
    # 3-B. 定価販売（実験 1, 2, 4）
    # -----------------------------------------------------------
    else:
        random.shuffle(candidates)

        for p in candidates:
            if stock <= 0:
                break

            desired = p.buy_primary

            if cond == 1:
                desired = min(desired, stock)     # 実験1は複数可
            else:
                desired = min(desired, 1, stock)  # 実験2・4は1点制限

            p.units_bought_primary = desired
            p.primary_bought = True
            p.primary_paid = C.PRIMARY_PRICE * desired

            stock -= desired

    # 最終的な在庫を保存
    group.remaining_stock = stock




# ===============================================================
#   set_secondary_allocation   （二次市場の配分処理）
# ===============================================================

def set_secondary_allocation(group: Group):
    """
    SecondMarket のあとで呼び出して、
    二次市場の取引（誰が何個買えたか / 売れたか）を決める。
    C案：1商品ずつ、最大買値が高い人に売る方式。
    """

    players = group.get_players()
    cond = group.subsession.condition

    # グループ全体サマリの初期化
    group.secondary_buyers_count = 0
    group.secondary_items_for_sale = 0
    group.secondary_trades_count = 0
    group.secondary_total_trade_value = cu(0)

    # いったん二次市場の結果をリセット
    for p in players:
        p.units_bought_secondary = 0
        p.units_sold_secondary = 0
        p.secondary_spent = cu(0)
        p.secondary_earned = cu(0)

    # ---------------------------
    # 1. 売りに出ている「商品」を1個ずつのリストにする
    #    （1人が2個持っている場合は2エントリ）
    # ---------------------------
    items_for_sale = []  # 要素：dict(seller=Player, ask=Currency, unit_index=1/2)

    for p in players:
        if p.p_role == "reseller" and p.units_bought_primary > 0:
            # 1個目
            ask1 = p.field_maybe_none("resale_price")
            if ask1 is not None:
                items_for_sale.append(dict(seller=p, ask=ask1, unit_index=1))

            # 実験1で2個持っていて、2個目の価格も入っている場合
            if cond == 1 and p.units_bought_primary >= 2:
                ask2 = p.field_maybe_none("resale_price_2")
                if ask2 is not None:
                    items_for_sale.append(dict(seller=p, ask=ask2, unit_index=2))

    # ★ 出品点数
    group.secondary_items_for_sale = len(items_for_sale)


    # ---------------------------
    # 2. 買い手リストを作る（一次で買えず、二次市場で購入希望した consumer/fan）
    # ---------------------------
    buyers = [
        p for p in players
        if p.p_role in ["consumer", "fan"]
        and p.units_bought_primary == 0
        and p.buy_secondary is True
        and p.secondary_price is not None
    ]

    # 最大買値が高い順にソート
    buyers.sort(key=lambda pl: pl.secondary_price, reverse=True)

    # ★ 二次市場に参加した買い手人数
    group.secondary_buyers_count = len(buyers)


    # ---------------------------
    # 3. 各商品について、まだ買っていない買い手の中から
    #    「secondary_price >= ask」の人を探し、いちばん高い人に売る
    # ---------------------------
    for item in items_for_sale:
        seller = item["seller"]
        ask = item["ask"]

        chosen_buyer = None

        for b in buyers:
            if b.secondary_price >= ask:
                chosen_buyer = b
                break  # secondary_price の降順なので、最初に見つかった人がベスト

        if chosen_buyer is not None:
            # 取引価格はシンプルに「売り手の提示価格 = ask」とする
            trade_price = ask

            # 取引成立！
            seller.units_sold_secondary += 1
            chosen_buyer.units_bought_secondary += 1

            # 金額の記録
            seller.secondary_earned += trade_price
            chosen_buyer.secondary_spent += trade_price

            # この買い手は1個買ったので、リストから外す（1人1個まで）
            buyers.remove(chosen_buyer)
        else:
            # この商品は売れ残り（何もしない）
            pass


    # ---------------------------
    # 取引件数と総取引額を集計
    # ---------------------------
    group.secondary_trades_count = sum(p.units_sold_secondary for p in players)
    group.secondary_total_trade_value = sum(p.secondary_earned for p in players)
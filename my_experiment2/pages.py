from otree.api import *
from .models import C, Subsession, Group, Player


# ============================================================
#   Consent（インフォームドコンセント）
# ============================================================

class Consent(Page):
    form_model = "player"
    form_fields = ["consent", "student_id"]

    def is_displayed(self):
        # ラウンド1のときだけ表示
        return self.subsession.round_number == 1
    
    def error_message(player, values):
        consent = values.get("consent")
        student_id = values.get("student_id")

        if not consent:
            return "内容をご確認の上、「上記の内容に同意し、実験に協力します」にチェックを入れてください。"

        if not student_id or student_id.strip() == "":
            return "学籍番号を入力してください。"


# ============================================================
# Introduction（実験の説明）
# ============================================================

class Introduction(Page):
    form_model = "player"
    form_fields = ["scenario_read"]

    def is_displayed(self):
        # ラウンド1のときだけ表示
        return self.subsession.round_number == 1

    def error_message(player, values):
        if not values.get("scenario_read"):
            return "内容をよく読んだうえで、「理解しました」にチェックを入れてください。"


# ============================================================
# Role（役割の割り振りと説明）
# ============================================================

class Role(Page):
    form_model = "player"
    form_fields = ["role_read"]

    def is_displayed(self):
        # ラウンド1のときだけ表示
        return self.subsession.round_number == 1
    
    def vars_for_template(player):
        role = player.p_role   # consumer / fan / reseller

        # 留保価格を安全に取得
        reservation = player.field_maybe_none('reservation_price')
        reservation_price = int(reservation) if reservation is not None else None

        # ★ 日本語名（ここだけ特別表示）
        role_jp = {
            "consumer": "消費目的消費者（consumer）",
            "fan": "ファンクラブ会員消費者（fan）",
            "reseller": "転売目的消費者（reseller）",
        }.get(role, role)

        # 役割ごとの説明文（好きに書き換えてOK）
        explanations = {
            "consumer": (
                "あなたはこのフィギュアを<strong>「自分自身で楽しむために」</strong>欲しいと考えています。<br>"
                "この商品に対してあなたが“最大支払ってもよい”と考える金額が「留保価格」です。<br><br>"
                "あなたの余剰（利得）は次のように計算されます：<br>"
                "　・商品を購入した場合：<strong>　余剰　＝　留保価格　−　実際に支払った金額<strong><br>"
                "　・購入しなかった場合：<strong>　   余剰　＝　0</strong><br><br>"
            ),
            "fan": (
                "あなたはそのキャラクターの熱心なファンです。<br>"
                "あなたはこのフィギュアを<strong>「自分自身で楽しむために」</strong>欲しいと考えています。<br>"
                "この商品に対してあなたが“最大支払ってもよい”と考える金額が「留保価格」です。<br><br>"
                "あなたの余剰（利得）は次のように計算されます：（※ファンクラブの諸費用に関して、本実験では考えないものとする）<br>"
                "　・商品を購入した場合：<strong>　余剰　＝　留保価格　−　実際に支払った金額</strong><br>"
                "　・購入しなかった場合：<strong>　余剰　＝　0</strong><br>"
            ),
            "reseller": (
                "あなたはこのフィギュアを「自分のために」ではなく、<strong>二次市場で売却し、利益を得ることを目的</strong>としています。<br>"
                "一次市場で商品を購入し、二次市場で売却することで利益を得られます。<br><br>"
                "あなたの余剰（利得）は次のように計算されます：<br>"
                "　・二次市場で売れた場合：<strong>　余剰　＝　二次市場での売値　−　一次市場で購入価格</strong><br>"
                "　・　売れなかった場合　：<strong>　余剰　＝　0　−　一次市場で購入価格</strong>　（※仕入れた分だけ損失になる）<br><br>"
            ),
        }

        explanation = explanations.get(role, "")

        return dict(
            role_jp=role_jp,
            reservation_price=reservation_price,
            explanation=explanation,
        )

    @staticmethod
    def error_message(player, values):
        if not values.get("role_read"):
            return "説明をよく読んだ上で、「理解しました」にチェックを入れてください。"




# ============================================================
# FirstMarket（一次市場）
# ============================================================

class FirstMarket(Page):
    form_model = "player"

    def get_form_fields(player):
        cond = player.subsession.condition

        # 実験3・5 → buy_primary と bid_primary の2つを出す
        if cond in [3, 5]:
            return ["buy_primary", "bid_primary"]

        # それ以外 → buy_primary だけ
        return ["buy_primary"]


    def vars_for_template(player):
        cond = player.subsession.condition
        role = player.p_role   # ★ 役割を先に取る

        titles = {
            1: "実験1：通常販売",
            2: "実験2：個数制限",
            3: "実験3：オークション",
            4: "実験4：ファン先行＋通常販売",
            5: "実験5：ファン先行＋オークション",
        }

        explanations = {
            1: (
                "商品が1000円で販売されています。販売点数は2点です。<br><br>"
                "この実験では、一人当たり最大2点まで購入することができます。<br>"
                "あなたはこの商品を何点購入したいですか？"
            ),
            2: (
                "商品が1000円で販売されています。販売点数は2点です。<br><br>"
                "この実験では、個数制限が設けられており、購入は一人当たり「1点まで」です。<br>"
                "あなたはこの商品を購入したいですか？"
            ),
            3: (
                "この実験ではオークションで商品の価格を決定します。<br><br>"
                "この商品が欲しいのなら、オークションに参加し、かつ落札しなければなりません。<br>"
                "オークション参加者の入札額をもとに、落札者が決まります。<br>"
                "販売個数は2で、一番目と二番目に高い価格を入札した人が落札者となります。<br>"
                "ただし、三番目に高い入札額で支払います。<br>"
                "※入札が同額になり、上位2名が決められない場合は、ランダムにコンピュータが落札者を決定します。<br><br>"
                "あなたはオークションに参加しますか？<br>"
                "したい場合は、オークションの入札額も入力してください。"
            ),
            4: (
                "商品が1000円で販売されています。販売点数は2点です。<br><br>"
                "この実験では、まずファンクラブ会員（fan）のみ購入可能な先行販売（1点）が実施され、その後、一般消費者向けに残りの在庫（1点）を販売します。<br>"
                "商品の価格はどちらの場合も、定価の1000円です。<br>fanが先行販売で「購入したい」を選んだ場合、そのfanは必ず1点購入できます。<br>"
                "fanが「購入しない」を選んだ場合には、2点とも一般向け販売に回ります。<br><br>あなたはこの商品を購入したいですか？<br><br>"
                "※ファンクラブ会員とは役割が「fan」のプレイヤーのことを指し、「consumer」はファンクラブ会員ではありません。"
            ),
            5: (
                "この実験では、まずファンクラブ会員（fan）のみ購入可能な先行販売（1点）が実施され、その後、一般消費者向けに残りの在庫（1点）を販売します。<br><br>"
                "商品の価格は先行販売時は定価の1000円ですが、一般販売ではオークションで商品の価格が決まります。<br><br>"
                "ファンクラブ会員（fan）が先行販売で「購入したい」を選んだ場合、残り1点のみがオークションにかけられます。<br>"
                "fanが「購入しない」を選んだ場合には、2点ともオークションにかけられます。<br><br>"
                "あなたがファンクラブ会員ではなく、この商品が欲しいのなら、オークションに参加し、かつ落札しなければなりません。<br>"
                "オークション参加者の入札額をもとに、落札者が決まります。<br>"
                "落札者は一番高い価格を入札した人です。ただし、二番目に高い入札額を支払います。<br>"
                "2名以上が同額で一番高い入札をした場合は、ランダムにコンピュータが落札者を決定します。<br><br>"
                "あなたはこの商品を購入したいですか？<br>したい場合は、オークションの入札額も入力してください。<br><br>"
                "※ファンクラブ会員とは役割が「fan」のプレイヤーのことを指し、「consumer」はファンクラブ会員ではありません。"
             ),
        }

        explanation = explanations.get(cond, "")

        # ★ 実験1 かつ consumer / fan のときだけ、2点目の余剰について追加
        if cond == 1 and role in ["consumer", "fan"]:
            explanation += (
                "<br><br>"
                "ただし、consumer / fan の方については、"
                "このフィギュアから得られる価値は<strong>1点目のみ</strong>に対して発生すると仮定します。<br>"
                "2点目を購入しても、余剰（利得）は増えません。<br>"
                "（つまり、1点購入した場合も2点購入した場合も、"
                "余剰の計算は<strong>「留保価格 − 1点分の支払額」</strong>で行われます。）"
            )

        if cond == 1:
            choices = [
                [1, "1点購入したい"],
                [2, "2点購入したい"],
                [0, "購入しない"],
            ]
        else:
            choices = [
                [1, "購入したい"],
                [0, "購入しない"],
            ]

        # field_maybe_none() で安全に取得
        reservation = player.field_maybe_none('reservation_price')

        # None でなければ int に変換
        if reservation is not None:
            reservation_price = int(reservation)
        else:
            reservation_price = None

        return dict(
            experiment_no=cond,
            title=titles.get(cond, ""),
            explanation=explanation,
            role=player.p_role,
            reservation_price=reservation_price,
            choices=choices,
        )

    def error_message(player, values):
        cond = player.subsession.condition
        buy = values.get("buy_primary")
        bid = values.get("bid_primary")
        reservation = player.field_maybe_none('reservation_price')
        role = player.p_role

        # ★ 共通：購入するかどうかを必ず選ばせる
        if buy is None:
            return "購入意向を選択してください。"

        # ★ 実験3・5だけチェック
        if cond in [3, 5]:

            # -----------------------------
            # 実験5の fan は「先行販売で定価購入」
            # → オークション入札は不要、むしろ禁止
            # -----------------------------
            if cond == 5 and role == "fan":
                # 購入したい（先行販売で1000円購入）
                if buy == 1:
                    # 何か入札額を入れていたらエラー
                    if bid is not None and bid > 0:
                        return "ファンクラブ会員は先行販売で定価1000円で購入できます。オークション入札は不要です。入札額は入力しないでください。"

                # 購入しないのに入札している
                if buy == 0:
                    if bid is not None and bid > 0:
                        return "オークションに参加しない場合は入札額を入力しないでください。"

                # fan のときはここで終了（オークションチェックはこれで完了）
                return

            # -----------------------------
            # それ以外（実験3の全員＋実験5の consumer / reseller）
            # → いままでのオークションルールを適用
            # -----------------------------

            # ① オークションに参加する（buy != 0）のに入札がない
            if buy != 0:
                if bid is None or bid <= 0:
                    return "オークションに参加する場合は入札額を入力してください。"

            # ② オークションに参加しない（buy = 0）のに入札している
            if buy == 0:
                if bid is not None and bid > 0:
                    return "オークションに参加しない場合は入札額を入力しないでください。"

            # ③ 留保価格を超える入札は禁止
            if reservation is not None and bid is not None:
                if bid > reservation:
                    return f"あなたの留保価格（{int(reservation)}円）を超える入札はできません。"


# ============================================================
# WaitPage（一次市場の割り当て）
# ============================================================

class PrimaryWaitPage(WaitPage):
    after_all_players_arrive = "set_primary_allocation"


# ============================================================
# AuctionResult（オークション結果）
# ============================================================

class AuctionResult(Page):
    def is_displayed(player):
        # 実験3と5（オークションがある条件）のときだけ表示
        return player.subsession.condition in [3, 5]

    def vars_for_template(player):
        g = player.group
        me = player
        players = g.get_players()

        rows = []
        for p in players:
            bid = p.field_maybe_none("bid_primary")

            rows.append(dict(
                id_in_group=p.id_in_group,
                role=p.p_role,
                bid=bid,
                units=p.units_bought_primary,
                paid=p.primary_paid,
                is_me=(p.id == me.id),
                is_winner=(p.units_bought_primary > 0),
            ))

        # 入札額の降順でソート（入札なしは下）
        rows.sort(
            key=lambda r: 0 if r["bid"] is None else float(r["bid"]),
            reverse=True,
        )

        # ---------- ★ 追加：落札者と非落札者の境界 index を特定 ----------
        boundary_index = None
        for i in range(len(rows) - 1):
            if rows[i]["is_winner"] and not rows[i+1]["is_winner"]:
                boundary_index = i
                break

        return dict(
            auction_rows=rows,
            boundary_index=boundary_index,
        )



# ============================================================
# SecondMarket（二次市場）
# ============================================================

class SecondMarket(Page):
    form_model = "player"
    form_fields = ['buy_secondary', 'secondary_price', 'resale_price', 'resale_price_2']

    def is_displayed(self):
        return True

    def get_form_fields(player):
        p = player
        cond = p.subsession.condition
        fields = []

        # reseller で一次で買えた → 売値を聞く
        if p.p_role == "reseller" and p.units_bought_primary > 0:
            fields.append("resale_price")
             # ★ 実験1で2点買っているときだけ2点目も聞く
            if cond == 1 and p.units_bought_primary == 2:
                fields.append("resale_price_2")

        # 一次で買えなかった人 → 二次市場で買うか？
        if p.units_bought_primary == 0 and p.p_role != "reseller":
            fields.append("buy_secondary")
            fields.append("secondary_price")

        return fields

    def vars_for_template(player):
        cond = player.subsession.condition

        titles = {
            1: "実験1：通常販売",
            2: "実験2：個数制限",
            3: "実験3：オークション",
            4: "実験4：ファン先行＋通常販売",
            5: "実験5：ファン先行＋オークション",
        }

        role = player.p_role  # consumer / fan / reseller
        bought_primary = player.primary_bought  # True / False

        explanations = {
            "consumer_bought": "一次市場での販売の結果、あなたは商品を購入できました。",
            "consumer_not_bought": (
                "一次市場での販売の結果、あなたは商品を購入できませんでした。<br><br>さて、同一未使用の商品がフリマアプリで出品されています。<br>あなたその商品の購入を希望しますか？<br>購入を希望する場合は希望金額も入力してください。"
            ),
            "reseller_bought": (
                "一次市場での販売の結果、あなたは商品を購入できました。<br><br>さて、あなたはこの商品を未使用のまま、フリマアプリに出品できます。<br>何円で出品しますか？"
            ),
            "reseller_not_bought": "一次市場での販売の結果、あなたは商品を購入できませんでした。"
        }

        if role in ["consumer", "fan"]:
            explanation = (
                explanations["consumer_bought"]
                if bought_primary else explanations["consumer_not_bought"]
            )
        elif role == "reseller":
            explanation = (
                explanations["reseller_bought"]
                if bought_primary else explanations["reseller_not_bought"]
            )
        else:
            explanation = ""

        show_buy_secondary = (player.units_bought_primary == 0 and player.p_role != "reseller")


        # field_maybe_none() で安全に取得
        reservation = player.field_maybe_none('reservation_price')

        # None でなければ int に変換
        if reservation is not None:
            reservation_price = int(reservation)
        else:
            reservation_price = None

        # ★ 追加：留保価格分布をテンプレに渡す
        consumer_values_str = ", ".join(str(v) for v in C.CONSUMER_VALUES)
        fan_values_str = ", ".join(str(v) for v in C.FAN_VALUES)
        group_structure_text = "consumer 2人, fan 1人, reseller 2人"

        return dict(
            experiment_no=cond,
            title=titles.get(cond, ""),
            explanation=explanation,
            role=player.p_role,
            units_bought_primary=player.units_bought_primary,
            reservation_price=reservation_price,
            show_buy_secondary=show_buy_secondary,
            consumer_values_str=consumer_values_str,
            fan_values_str=fan_values_str,
            group_structure_text=group_structure_text,
        )

    def error_message(player, values):
        p = player
        buy_sec = values.get("buy_secondary")
        sec_price = values.get("secondary_price")
        resale_price = values.get("resale_price")
        resale_price_2 = values.get("resale_price_2")
        cond = p.subsession.condition

        # ★ 二次市場の購入意向を聞かれているのは
        #    「一次で買えていない consumer / fan」だけなので、
        #    その人たちにだけ必須チェックをかける
        if p.units_bought_primary == 0 and p.p_role != "reseller":
            if buy_sec is None:
                return "購入意向を選択してください。"

        # ① 一次で買えず & 「二次市場で購入する」を選んだ場合：価格必須
        if p.units_bought_primary == 0 and buy_sec is True:
            # 希望金額が入っていない／0以下
            if sec_price is None or sec_price <= 0:
                return "購入を希望する場合は、空欄に価格を入力してください。"
            # 留保価格を超える希望金額は禁止
            reservation = p.field_maybe_none('reservation_price')
            if reservation is not None and sec_price is not None:
                if sec_price > reservation:
                    return f"あなたの留保価格（{int(reservation)}円）を超える価格は入力できません。"
        
        # ② 一次で買えず & 「二次市場では購入しない」を選んだ場合：価格を入れてはいけない
        if p.units_bought_primary == 0 and buy_sec is False:
            # 何かしら値が入っていたらエラー（None なら未入力）
            if sec_price is not None and sec_price > 0:
                return "購入を希望しない場合は、空欄に価格を入力しないでください。"

        # ③ reseller で一次購入あり → 売値必須
        if p.p_role == "reseller" and p.units_bought_primary > 0:
            if resale_price is None:
                return "空欄に価格を入力してください。"
            
            # ★ 実験1で2点買っているとき：2点目も必須
            if cond == 1 and p.units_bought_primary == 2:
                if resale_price_2 is None or resale_price_2 <= 0:
                    return "2点目の価格を入力してください。<br>1点目と同額を設定する場合でも入力は必須です。"

            # ★ 実験1以外 or 1点しか買っていないのに2つ目を書いたらエラー
            if (cond != 1 or p.units_bought_primary < 2) and resale_price_2 is not None and resale_price_2 > 0:
                return "1点しか商品を購入していない場合は、2点目の欄には何も入力しないでください。"


# ============================================================
# WaitPage（二次市場の割り当て）
# ============================================================

class SecondaryWaitPage(WaitPage):
    after_all_players_arrive = "set_secondary_allocation"


# ============================================================
# SecondaryResult（二次市場の結果表示）
# ============================================================

class SecondaryResult(Page):
    def is_displayed(player):
        # 二次市場ページをやったあと全員に見せる想定なら True でOK
        return True

    def vars_for_template(player):
        p = player
        g = player.group

        cond = player.subsession.condition

        titles = {
            1: "実験1：通常販売",
            2: "実験2：個数制限",
            3: "実験3：オークション",
            4: "実験4：ファン先行＋通常販売",
            5: "実験5：ファン先行＋オークション",
        }

        # --- あなたの状況メッセージ ---

        # 買い希望（None-safe）
        buy_sec = p.field_maybe_none('buy_secondary')

        # ★ 売り手として売却を希望したかどうか
        sell_intent = (
            p.p_role == "reseller"
            and p.units_bought_primary > 0
            and (
                p.field_maybe_none('resale_price') is not None or
                p.field_maybe_none('resale_price_2') is not None
            )
        )

        if p.units_bought_secondary > 0:
            my_status = "あなたは二次市場で商品を購入しました。"

        elif p.units_sold_secondary > 0:
            my_status = "あなたは二次市場で商品を販売しました。"

        elif buy_sec is True:
            my_status = "あなたは二次市場で購入を希望しましたが、今回は取引が成立しませんでした。"

        elif sell_intent:
            my_status = "あなたは二次市場で売却を希望しましたが、今回は取引が成立しませんでした。"

        else:
            my_status = "あなたは二次市場での取引には参加しませんでした。"
        
        # --- None-safe 金額処理 ---
        spent = p.field_maybe_none('secondary_spent')
        earned = p.field_maybe_none('secondary_earned')
        spent = spent if spent is not None else 0
        earned = earned if earned is not None else 0

        # --- グループ全体の二次市場サマリ（set_secondary_allocation で集計済み）---
        buyers_count   = g.secondary_buyers_count          # 買い手人数
        items_for_sale = g.secondary_items_for_sale        # 出品点数
        trades         = g.secondary_trades_count          # 成立件数
        total_value    = g.secondary_total_trade_value     # 取引総額

        # 成立取引があれば平均価格を計算
        avg_price = total_value / trades if trades > 0 else None

        return dict(
            my_status=my_status,
            title=titles.get(cond, ""),
            buyers_count=buyers_count,
            items_for_sale=items_for_sale,
            trades=trades,
            avg_price=avg_price,

            # ←★ NEW：テンプレート用変数として渡す
            units_bought_secondary=p.units_bought_secondary,
            units_sold_secondary=p.units_sold_secondary,
            secondary_spent=spent,
            secondary_earned=earned,
        )




# ============================================================
# Results（結果表示）
# ============================================================

class Results(Page):
    def is_displayed(player):
        # 全ラウンドで表示する想定なら True でOK
        return True

    def vars_for_template(player):
        p = player
        g = p.group
        cond = p.subsession.condition

        # 実験タイトル（他ページと合わせておく）
        titles = {
            1: "実験1：通常販売",
            2: "実験2：個数制限",
            3: "実験3：オークション",
            4: "実験4：ファン先行＋通常販売",
            5: "実験5：ファン先行＋オークション",
        }
        title = titles.get(cond, "")

        role = p.p_role  # 'consumer' / 'fan' / 'reseller'

        # 留保価格（ない人は None）
        reservation = p.field_maybe_none("reservation_price")
        reservation_price = int(reservation) if reservation is not None else None

        # ===== 一次市場 =====
        units_primary = p.units_bought_primary
        primary_paid = p.primary_paid

        # 一次余剰
        if role in ["consumer", "fan"]:
            if units_primary > 0:
                # 価値は1点目だけと仮定 → 1点あたりの支払額を引く
                per_unit_price = primary_paid / units_primary
                primary_surplus = reservation - per_unit_price
            else:
                primary_surplus = cu(0)
        else:
            # reseller は一次の時点ではまだ利益ゼロ
            primary_surplus = cu(0)

        # ===== 二次市場 =====
        units_bought_secondary = p.units_bought_secondary
        units_sold_secondary = p.units_sold_secondary

        # 取引成立したか？
        trade_occurred = (units_bought_secondary > 0 or units_sold_secondary > 0)

        # 表示用の「取引価格」
        if not trade_occurred:
            trade_price = None
        else:
            if units_bought_secondary > 0:
                # consumer / fan は最大1点なので、そのまま支払額 = 取引価格
                trade_price = p.secondary_spent
            elif units_sold_secondary > 0:
                # reseller が複数売った場合は平均価格にしておく
                if units_sold_secondary == 1:
                    trade_price = p.secondary_earned
                else:
                    trade_price = p.secondary_earned / units_sold_secondary
            else:
                trade_price = None

        # 二次余剰
        if role in ["consumer", "fan"]:
            if units_bought_secondary > 0:
                # 二次で購入した場合： 留保価格 − 実際に払った金額
                secondary_surplus = reservation - p.secondary_spent
            else:
                secondary_surplus = cu(0)
        else:
            # reseller の利益：
            # ・売れた場合：二次での売上 − 一次での仕入れ
            # ・売れなかった場合：0 − 一次での仕入れ
            secondary_surplus = p.secondary_earned - p.primary_paid

        total_surplus = primary_surplus + secondary_surplus

        return dict(
            title=title,
            role=role,
            reservation_price=reservation_price,

            units_bought_primary=units_primary,
            primary_paid=primary_paid,
            primary_surplus=primary_surplus,

            trade_occurred=trade_occurred,
            trade_price=trade_price,
            secondary_surplus=secondary_surplus,

            total_surplus=total_surplus,
        )

# ============================================================
# RoundSyncWaitPage（次のラウンドまでの待ち）
# ============================================================

class RoundSyncWaitPage(WaitPage):
    wait_for_all_players = True   # グループ全員が来るまで待つ

    # 最終ラウンドでは出したくない場合はこれを付ける
    def is_displayed(player):
        return player.subsession.round_number < C.NUM_ROUNDS

    # 画面に出す固定テキスト（簡単なのでここに直書きでもOK）
    body_text = "他の参加者が結果ページを確認するのを待っています。次のラウンドまでしばらくお待ちください。"


# ============================================================
# ページ順序
# ============================================================

page_sequence = [
    Consent,
    Introduction,
    Role,
    FirstMarket,
    PrimaryWaitPage,
    AuctionResult,
    SecondMarket,
    SecondaryWaitPage, 
    SecondaryResult,
    Results,
    RoundSyncWaitPage,
]

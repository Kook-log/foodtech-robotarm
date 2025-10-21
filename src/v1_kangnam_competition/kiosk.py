import flet as ft
import json
import os
from datetime import datetime
import hashlib

# 메뉴 데이터
MENU_DATA = {
    "메인 메뉴": [
        {"name": "토스트", "price": 100, "image": "🥪"}
    ]
}

# (미사용) 토핑 옵션 - 기존 구조 보존만, 사용하지 않음
TOPPING_OPTIONS = []

class OrderManager:
    """주문 데이터 관리 클래스"""
    def __init__(self):
        self.orders_file = "orders.json"
        self.load_orders()
    
    def load_orders(self):
        if os.path.exists(self.orders_file):
            with open(self.orders_file, 'r', encoding='utf-8') as f:
                self.orders = json.load(f)
        else:
            self.orders = []
    
    def save_order(self, order_data):
        self.orders.append(order_data)
        with open(self.orders_file, 'w', encoding='utf-8') as f:
            json.dump(self.orders, f, ensure_ascii=False, indent=2)
    
    def get_next_order_number(self):
        if not self.orders:
            return 1
        return max([order.get('order_number', 0) for order in self.orders]) + 1


class KioskApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "토스트랩 키오스크"
        self.page.window.width = 1024
        self.page.window.height = 768
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0

        self.order_manager = OrderManager()
        self.order_type = "매장"   # 매장/포장

        # 상태
        self.current_item = None
        self.qty = 1
        self.qty_text = ft.Text("1", size=18)
        self.total_label = ft.Text("", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.YELLOW_700)

        # 옵션 선택 라디오 그룹(토스트용)
        self.opt_bread = None
        self.opt_ham = None
        self.opt_sauce = None
        self.opt_cheese = None

        self.current_view = "start"  # start | info | order | options
        self.show_start_view()

    # ---------- 공통 ----------
    def close_dialog(self, dialog):
        dialog.open = False
        self.page.update()

    def clear_and_update(self):
        self.page.controls.clear()
        self.page.overlay.clear()
        self.page.update()

    # ---------- 뷰: 시작(토스트 테마, 아무데나 클릭 → 옵션 선택) ----------
    def show_start_view(self):
        self.current_view = "start"
        self.clear_and_update()

        title = ft.Text("ToastLab", size=64, weight=ft.FontWeight.BOLD, color=ft.Colors.BROWN)
        subtitle = ft.Text("화면을 터치하면 주문을 시작합니다", size=22, color=ft.Colors.GREY_700)

        hero = ft.Container(
            content=ft.Column(
                [
                    ft.Text("🥪", size=180),
                    title,
                    subtitle,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8
            ),
            padding=ft.padding.only(top=120, bottom=60),
            alignment=ft.alignment.center
        )

        # 화면 전체를 클릭하면 옵션 선택 화면으로
        self.page.add(
            ft.Container(
                on_click=lambda e: self.show_toast_options_view(),  # ← 핵심
                content=ft.Column(
                    [hero],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                expand=True, alignment=ft.alignment.center,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center, end=ft.alignment.bottom_center,
                    colors=[ft.Colors.AMBER_50, ft.Colors.WHITE],
                ),
            )
        )
        self.page.update()

    # ---------- 뷰: 토스트 옵션 선택 ----------
    def show_toast_options_view(self):
        self.current_view = "options"
        self.clear_and_update()

        # 기본 상품 설정
        self.current_item = MENU_DATA["메인 메뉴"][0]
        self.qty = 1
        self.qty_text.value = "1"

        # 주문 방식(매장/포장)
        order_type_rg = ft.RadioGroup(
            value=self.order_type,
            on_change=lambda e: setattr(self, "order_type", e.control.value),
            content=ft.Row([ft.Radio(value="매장", label="매장"), ft.Radio(value="포장", label="포장")])
        )

        # 4가지 옵션 라디오
        self.opt_bread = ft.RadioGroup(
            value="일반 식빵",
            content=ft.Row([
                ft.Radio(value="일반 식빵", label="일반 식빵"),
                ft.Radio(value="계란물 식빵", label="계란물 식빵"),
            ])
        )
        self.opt_ham = ft.RadioGroup(
            value="햄 1장",
            content=ft.Row([
                ft.Radio(value="햄 1장", label="햄 1장"),
                ft.Radio(value="햄 2장", label="햄 2장"),
            ])
        )
        self.opt_sauce = ft.RadioGroup(
            value="딸기잼",
            content=ft.Row([
                ft.Radio(value="딸기잼", label="딸기잼"),
                ft.Radio(value="이삭 소스", label="이삭 소스"),
            ])
        )
        self.opt_cheese = ft.RadioGroup(
            value="치즈 O",
            content=ft.Row([
                ft.Radio(value="치즈 O", label="치즈 O"),
                ft.Radio(value="치즈 X", label="치즈 X"),
            ])
        )

        # 수량 스테퍼
        qty_row = ft.Row(
            [
                ft.IconButton(icon=ft.Icons.REMOVE_CIRCLE_OUTLINE, on_click=lambda e: self._change_qty_toast(-1)),
                self.qty_text,
                ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=lambda e: self._change_qty_toast(1)),
            ],
            alignment=ft.MainAxisAlignment.START,
        )

        # 합계(옵션가 없음 → 기본가 × 수량)
        self._update_total_label_toast()

        header = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(icon=ft.Icons.HOME, icon_color=ft.Colors.WHITE,
                                  on_click=lambda e: self.show_start_view()),
                    ft.Text("토스트 구성 선택", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor=ft.Colors.YELLOW_700, padding=20, height=80,
        )

        # 카드 컴포넌트 함수
        def section_card(title_text, inner_control):
            return ft.Container(
                content=ft.Column(
                    [ft.Text(title_text, size=18, weight=ft.FontWeight.BOLD), inner_control],
                    spacing=10
                ),
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=12,
                padding=16
            )

        body = ft.Container(
            content=ft.Column(
                [
                    # 상단 요약
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(self.current_item["image"], size=60),
                                ft.Column(
                                    [
                                        ft.Text(self.current_item["name"], size=20, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"기본가: {self.current_item['price']:,}원", color=ft.Colors.GREY_700),
                                        order_type_rg,
                                    ], spacing=6
                                )
                            ],
                            alignment=ft.MainAxisAlignment.START
                        ),
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=12,
                        padding=16
                    ),

                    section_card("1) 빵 선택", self.opt_bread),
                    section_card("2) 햄 선택", self.opt_ham),
                    section_card("3) 소스 선택", self.opt_sauce),
                    section_card("4) 치즈 선택", self.opt_cheese),

                    ft.Container(
                        content=ft.Row(
                            [ft.Text("수량", size=18, weight=ft.FontWeight.BOLD), qty_row],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=12,
                        padding=16
                    ),

                    ft.Divider(),
                    ft.Row([self.total_label], alignment=ft.MainAxisAlignment.END),

                    ft.Row(
                        [
                            ft.ElevatedButton("이전", on_click=lambda e: self.show_start_view()),
                            ft.FilledButton("주문하기", on_click=self._confirm_and_complete_order_toast),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=16
            ),
            expand=True, padding=20, bgcolor=ft.Colors.GREY_100
        )

        self.page.add(header, body)
        self.page.update()

    # ---------- 합계/수량(토스트용) ----------
    def _change_qty_toast(self, delta):
        self.qty = max(1, self.qty + delta)
        self.qty_text.value = str(self.qty)
        self._update_total_label_toast()
        self.page.update()

    def _calc_total_toast(self):
        base = self.current_item["price"]
        return base * self.qty

    def _update_total_label_toast(self):
        total = self._calc_total_toast()
        self.total_label.value = f"합계: {total:,}원  (수량 {self.qty}개)"

    # ---------- 주문 완료(토스트 옵션 저장) ----------
    def _confirm_and_complete_order_toast(self, e):
        total = self._calc_total_toast()
        options = {
            "빵": self.opt_bread.value,
            "햄": self.opt_ham.value,
            "소스": self.opt_sauce.value,
            "치즈": self.opt_cheese.value,
        }

        order_number = self.order_manager.get_next_order_number()
        order_data = {
            "order_number": order_number,
            "timestamp": datetime.now().isoformat(),
            "order_type": self.order_type,
            "items": [
                {
                    "name": self.current_item["name"],
                    "base_price": self.current_item["price"],
                    "quantity": self.qty,
                    "options": options,
                    "image": self.current_item["image"],
                }
            ],
            "total": total
        }
        self.order_manager.save_order(order_data)

        completion_dialog = ft.AlertDialog(
            title=ft.Text("주문 완료", size=24, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=60),
                        ft.Text(f"주문번호: {order_number}", size=28, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{self.order_type} 주문이 접수되었습니다.", size=16),
                        ft.Text(
                            f"{self.current_item['name']} x{self.qty} "
                            f"({options['빵']}, {options['햄']}, {options['소스']}, {options['치즈']})",
                            size=14, color=ft.Colors.GREY_700),
                        ft.Text(f"총 결제금액: {total:,}원", size=16, weight=ft.FontWeight.BOLD),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6
                ),
                width=360, height=260,
            ),
            actions=[
                ft.ElevatedButton(
                    "확인",
                    on_click=lambda ev: (self.close_dialog(completion_dialog), self.show_start_view()),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.YELLOW_700, color=ft.Colors.WHITE),
                ),
            ],
        )
        self.page.overlay.append(completion_dialog)
        completion_dialog.open = True
        self.page.update()

    # ---------- (유지) 관리자 ----------
    def show_admin_login(self, e):
        password_field = ft.TextField(label="비밀번호", password=True, autofocus=True)

        def verify_password(ev):
            entered_password = hashlib.sha256(password_field.value.encode()).hexdigest()
            if entered_password == hashlib.sha256("admin1234".encode()).hexdigest():
                self.close_dialog(login_dialog)
                self.show_admin_panel()
            else:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("비밀번호가 올바르지 않습니다."))
                self.page.snack_bar.open = True
                self.page.update()
        
        login_dialog = ft.AlertDialog(
            title=ft.Text("관리자 로그인"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("관리자 비밀번호를 입력하세요:"),
                    password_field,
                    ft.Text("(기본 비밀번호: admin1234)", size=12, color=ft.Colors.GREY_600),
                ]),
                width=300, height=150,
            ),
            actions=[ft.TextButton("취소", on_click=lambda ev: self.close_dialog(login_dialog)),
                     ft.ElevatedButton("로그인", on_click=verify_password)],
        )
        self.page.overlay.append(login_dialog)
        login_dialog.open = True
        self.page.update()

    def show_admin_panel(self):
        orders_list = ft.Column(scroll=ft.ScrollMode.AUTO, height=400)
        self.order_manager.load_orders()

        if not self.order_manager.orders:
            orders_list.controls.append(ft.Text("주문 내역이 없습니다.", size=16, color=ft.Colors.GREY_600))
        else:
            for order in reversed(self.order_manager.orders[-20:]):
                order_time = datetime.fromisoformat(order["timestamp"])
                item = order["items"][0]
                # 옵션 요약 표시
                opt = item.get("options", {})
                opt_str = ""
                if opt:
                    opt_str = f" ({opt.get('빵','')}, {opt.get('햄','')}, {opt.get('소스','')}, {opt.get('치즈','')})"

                item_summary = f"{item['name']} x{item['quantity']}{opt_str}"

                order_card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"주문 #{order['order_number']}", weight=ft.FontWeight.BOLD),
                            ft.Text(order_time.strftime("%Y-%m-%d %H:%M"), color=ft.Colors.GREY_600),
                            ft.Text(f"{order['order_type']}", color=ft.Colors.YELLOW_700),
                            ft.Text(f"{order['total']:,}원", weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(item_summary, size=12, color=ft.Colors.GREY_700),
                    ]),
                    bgcolor=ft.Colors.GREY_100, border_radius=8, padding=10,
                    margin=ft.margin.only(bottom=10),
                )
                orders_list.controls.append(order_card)

        total_orders = len(self.order_manager.orders)
        total_revenue = sum(order.get("total", 0) for order in self.order_manager.orders)

        admin_dialog = ft.AlertDialog(
            title=ft.Text("관리자 패널", size=24, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text("전체 주문", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"{total_orders}건", size=20, weight=ft.FontWeight.BOLD),
                            ]),
                            bgcolor=ft.Colors.YELLOW_50, border_radius=8, padding=15, expand=True,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("전체 매출", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"{total_revenue:,}원", size=20, weight=ft.FontWeight.BOLD),
                            ]),
                            bgcolor=ft.Colors.GREEN_50, border_radius=8, padding=15, expand=True,
                        ),
                    ]),
                    ft.Divider(),
                    ft.Text("최근 주문 내역", size=18, weight=ft.FontWeight.BOLD),
                    orders_list,
                ], scroll=ft.ScrollMode.AUTO),
                width=600, height=600,
            ),
            actions=[ft.ElevatedButton("닫기", on_click=lambda e: self.close_dialog(admin_dialog))],
        )
        self.page.overlay.append(admin_dialog)
        admin_dialog.open = True
        self.page.update()


def main(page: ft.Page):
    KioskApp(page)

ft.app(target=main)

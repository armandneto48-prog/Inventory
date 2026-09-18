import os
import flet as ft


def main(page: ft.Page):
    page.title = "Ficha de Pedido do Cliente"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    LIMITE = 60.0
    valores = []

    # Componentes de Texto e Entradas
    titulo = ft.Text(
        "Ficha de Pedido do Cliente",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLUE_GREY_900,
    )
    ent_ficha = ft.TextField(label="Nº Ficha", keyboard_type=ft.KeyboardType.NUMBER)
    ent_nome = ft.TextField(label="Nome do Cliente")
    ent_contacto = ft.TextField(
        label="Contacto", keyboard_type=ft.KeyboardType.PHONE
    )

    ent_valor = ft.TextField(
        label="Novo Valor (€)", keyboard_type=ft.KeyboardType.NUMBER
    )
    lbl_packs = ft.Text("Packs: -", color=ft.Colors.GREY)
    lbl_total = ft.Text("TOTAL: 0.00 €", size=16, weight=ft.FontWeight.BOLD)

    lbl_status = ft.Text(
        "Aguardando dados...", size=14, weight=ft.FontWeight.BOLD
    )
    container_status = ft.Container(
        content=lbl_status,
        padding=10,
        border_radius=8,
        bgcolor=ft.Colors.GREY_200,
        alignment=ft.alignment.center,
    )
    barra_progresso = ft.ProgressBar(value=0, color=ft.Colors.GREEN)

    def atualizar_interface():
        total = sum(valores)
        texto = " + ".join([f"{v:.2f}€" for v in valores])
        lbl_packs.value = f"Packs: {texto}" if texto else "Packs: -"
        lbl_total.value = f"TOTAL: {total:.2f} €"

        pct = min(total / LIMITE, 1.0)
        barra_progresso.value = pct

        if total == 0:
            lbl_status.value = "Aguardando dados..."
            container_status.bgcolor = ft.Colors.GREY_200
            lbl_status.color = ft.Colors.BLACK
        elif total < 0.8 * LIMITE:
            lbl_status.value = f"DENTRO DO LIMITE | Margem: {LIMITE - total:.2f}€"
            container_status.bgcolor = ft.Colors.GREEN_400
            lbl_status.color = ft.Colors.WHITE
        elif total < LIMITE:
            lbl_status.value = (
                f"⚠️ PRÓXIMO DO LIMITE! Faltam: {LIMITE - total:.2f}€"
            )
            container_status.bgcolor = ft.Colors.AMBER_300
            lbl_status.color = ft.Colors.BLACK
        elif total == LIMITE:
            lbl_status.value = "🛑 ATENÇÃO: LIMITE EXATO DE 60.00€!"
            container_status.bgcolor = ft.Colors.RED_400
            lbl_status.color = ft.Colors.WHITE
        else:
            lbl_status.value = f"🚨 LIMITE ULTRAPASSADO! (+{total - LIMITE:.2f}€)"
            container_status.bgcolor = ft.Colors.RED_700
            lbl_status.color = ft.Colors.WHITE

        page.update()

    def adicionar_click(e):
        try:
            val = float(ent_valor.value.replace(",", "."))
            if val > 0:
                valores.append(val)
                ent_valor.value = ""
                atualizar_interface()
        except Exception:
            pass

    def limpar_click(e):
        valores.clear()
        ent_ficha.value = ""
        ent_nome.value = ""
        ent_contacto.value = ""
        ent_valor.value = ""
        atualizar_interface()

    # Layout da Interface
    page.add(
        titulo,
        ft.Divider(),
        ent_ficha,
        ent_nome,
        ent_contacto,
        ft.Divider(),
        ent_valor,
        ft.ElevatedButton(
            "+ Adicionar Valor",
            on_click=adicionar_click,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE,
        ),
        lbl_packs,
        lbl_total,
        ft.Divider(),
        container_status,
        barra_progresso,
        ft.Row(
            [
                ft.OutlinedButton("Limpar", on_click=limpar_click),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=port
    )   
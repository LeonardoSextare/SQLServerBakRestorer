import flet as ft

SAKURA = ft.Theme(
    color_scheme_seed="#AD1457",
    color_scheme=ft.ColorScheme(
        surface="#FFF2F6",
        secondary_container="#F48FB1",
        outline_variant="#E39AB4",
    ),
    scaffold_bgcolor="#FFDDE9",
    hover_color=ft.Colors.with_opacity(0.34, "#AD1457"),
    highlight_color=ft.Colors.with_opacity(0.24, "#AD1457"),
    splash_color=ft.Colors.with_opacity(0.30, "#AD1457"),
    focus_color=ft.Colors.with_opacity(0.28, "#AD1457"),
    navigation_rail_theme=ft.NavigationRailTheme(indicator_color="#F06292"),
)

OCEANO = ft.Theme(
    color_scheme_seed="#00B4D8",
    color_scheme=ft.ColorScheme(
        surface="#0B4F6C",
        surface_container_lowest="#093F57",
        surface_container_low="#0C5372",
        surface_container="#0E6382",
        surface_container_high="#11748F",
        surface_container_highest="#14839F",
        secondary_container="#1C8AAD",
        outline_variant="#2A93B8",
    ),
    scaffold_bgcolor="#0B4F6C",
    hover_color=ft.Colors.with_opacity(0.30, "#B8ECFF"),
    highlight_color=ft.Colors.with_opacity(0.22, "#B8ECFF"),
    splash_color=ft.Colors.with_opacity(0.26, "#B8ECFF"),
    focus_color=ft.Colors.with_opacity(0.24, "#B8ECFF"),
    navigation_rail_theme=ft.NavigationRailTheme(indicator_color="#1C8AAD"),
    card_theme=ft.CardTheme(color="#0E6382"),
)

FLORESTA = ft.Theme(
    color_scheme_seed="#7CD992",
    color_scheme=ft.ColorScheme(
        surface="#123A23",
        surface_container_lowest="#0D2E1B",
        surface_container_low="#143E26",
        surface_container="#1A4C2E",
        surface_container_high="#205C38",
        surface_container_highest="#266C42",
        secondary_container="#2C7D4C",
        outline_variant="#3B9160",
    ),
    scaffold_bgcolor="#123A23",
    hover_color=ft.Colors.with_opacity(0.30, "#CDF5D8"),
    highlight_color=ft.Colors.with_opacity(0.22, "#CDF5D8"),
    splash_color=ft.Colors.with_opacity(0.26, "#CDF5D8"),
    focus_color=ft.Colors.with_opacity(0.24, "#CDF5D8"),
    navigation_rail_theme=ft.NavigationRailTheme(indicator_color="#2C7D4C"),
    card_theme=ft.CardTheme(color="#1A4C2E"),
)

INDUSTRIAL = ft.Theme(
    color_scheme_seed="#FFA726",
    color_scheme=ft.ColorScheme(
        primary="#FFCE5B",
        on_primary="#2A1C00",
        surface="#272C31",
        surface_container_lowest="#1E2226",
        surface_container_low="#2C3238",
        surface_container="#373E45",
        surface_container_high="#414952",
        surface_container_highest="#4B545E",
        secondary_container="#55606B",
        outline_variant="#6B7783",
    ),
    scaffold_bgcolor="#272C31",
    hover_color=ft.Colors.with_opacity(0.28, "#FFD9A0"),
    highlight_color=ft.Colors.with_opacity(0.20, "#FFD9A0"),
    splash_color=ft.Colors.with_opacity(0.24, "#FFD9A0"),
    focus_color=ft.Colors.with_opacity(0.22, "#FFD9A0"),
    navigation_rail_theme=ft.NavigationRailTheme(indicator_color="#55606B"),
    card_theme=ft.CardTheme(color="#373E45"),
)

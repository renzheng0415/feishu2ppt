"""Semantic theme library for the OfficeCLI presentation engine V2."""


def _theme(name, bg, surface, ink, muted, primary, accent, border,
           heading="Microsoft YaHei", body="Microsoft YaHei", mono="Microsoft YaHei",
           series=None, dark=False):
    return {
        "name": name,
        "background": bg,
        "surface": surface,
        "ink": ink,
        "muted": muted,
        "primary": primary,
        "accent": accent,
        "border": border,
        "heading_font": "Microsoft YaHei",
        "body_font": "Microsoft YaHei",
        "mono_font": "Microsoft YaHei",
        "series": series or [primary, accent, muted, border],
        "dark": dark,
    }


THEMES = {
    # Executive and real-estate
    "realestate_gold": _theme(
        "地产黑金", "111111", "1C1C1C", "F8F8F6", "A1A1AA",
        "D4AF37", "F2D680", "333333", heading="Songti SC", dark=True,
        series=["D4AF37", "F2D680", "8C7853", "665A3A", "F8F8F6"],
    ),
    "executive_navy": _theme(
        "高管深蓝", "F6F8FB", "FFFFFF", "11233F", "607089",
        "1E3A5F", "E57A44", "DCE3EC", heading="Songti SC",
        series=["1E3A5F", "E57A44", "5E81AC", "88A2C2", "B8C6D8"],
    ),
    "financial_green": _theme(
        "金融墨绿", "F3F7F4", "FFFFFF", "163228", "66766E",
        "1F6B4F", "C89B3C", "D8E4DC", heading="Songti SC",
        series=["1F6B4F", "C89B3C", "4F8F73", "8AB59F", "D4C18A"],
    ),
    "architectural_sand": _theme(
        "建筑沙丘", "EFEAE0", "F9F7F2", "27231E", "716A60",
        "49423A", "B76E3C", "D7D0C4", heading="Songti SC",
        series=["49423A", "B76E3C", "8A8176", "C0A27A", "D6C7AE"],
    ),

    # Editorial and cultural
    "swiss_monocle": _theme(
        "瑞士墨水", "F4F2ED", "FFFFFF", "1A1917", "68645E",
        "C83E2B", "1A1917", "E5E1D7", heading="Songti SC",
        series=["C83E2B", "1A1917", "6F6A62", "B7B0A6", "E3DDD2"],
    ),
    "editorial_ink": _theme(
        "编辑部墨黑", "F7F5F0", "FFFEFB", "141414", "6F6B64",
        "141414", "B42318", "D9D4CA", heading="Songti SC",
        series=["141414", "B42318", "7D7469", "B9AFA2", "D8D0C5"],
    ),
    "terracotta_warm": _theme(
        "暖沙陶土", "FDFBF7", "F4EFE6", "2C221E", "6E615A",
        "C85A32", "6F8A78", "E6DDD0", heading="Songti SC",
        series=["C85A32", "6F8A78", "D09A76", "A98578", "E5C9AE"],
    ),
    "forest_canopy": _theme(
        "森林墨绿", "F5F1E8", "FFFFFF", "1A2E1F", "627066",
        "2D6A4F", "C69C48", "D8D3C8", heading="Songti SC",
        series=["2D6A4F", "C69C48", "6C9A7C", "A4B49E", "D4C6A5"],
    ),
    "autumn_amber": _theme(
        "金秋夕照", "FAF5EF", "FFFDF9", "332720", "786558",
        "D97706", "9F513D", "EBE1D5", heading="Songti SC",
        series=["D97706", "9F513D", "E3A857", "B88663", "E5C9A6"],
    ),

    # Minimal and product
    "vercel_minimal": _theme(
        "极简纯白", "FFFFFF", "FAFAFA", "000000", "666666",
        "000000", "0070F3", "E4E4E7",
        series=["000000", "0070F3", "666666", "A1A1AA", "D4D4D8"],
    ),
    "apple_keynote": _theme(
        "苹果发布会", "FAFAFA", "FFFFFF", "1D1D1F", "6E6E73",
        "0071E3", "AF52DE", "E5E5EA",
        series=["0071E3", "AF52DE", "34C759", "FF9F0A", "FF375F"],
    ),
    "brutalist_white": _theme(
        "新粗野纯白", "FFFFFF", "FFFFFF", "111111", "555555",
        "111111", "FF3B30", "111111",
        series=["111111", "FF3B30", "0057FF", "FFD400", "00A86B"],
    ),
    "bauhaus_primary": _theme(
        "包豪斯原色", "F7F3E8", "FFFCF5", "171717", "5C5C5C",
        "D62828", "1D4ED8", "171717",
        series=["D62828", "1D4ED8", "F2B705", "171717", "7A7A7A"],
    ),
    "soft_pastel": _theme(
        "柔雾粉彩", "FAF8FC", "FFFFFF", "2E2933", "7A7280",
        "8B7CF6", "F08BAE", "E8E2EE",
        series=["8B7CF6", "F08BAE", "6FC5B2", "F2C16B", "8FB7E8"],
    ),

    # Technology and dark
    "midnight_executive": _theme(
        "午夜蓝黑", "0D1117", "161B22", "F0F6FC", "8B949E",
        "2F81F7", "A371F7", "30363D", dark=True,
        series=["2F81F7", "A371F7", "3FB950", "D29922", "F85149"],
    ),
    "cyber_neocarbon": _theme(
        "赛博深光", "0B1020", "151D32", "F8FAFC", "94A3B8",
        "8B5CF6", "22D3EE", "283556", dark=True,
        series=["8B5CF6", "22D3EE", "F472B6", "34D399", "FBBF24"],
    ),
    "catppuccin_mauve": _theme(
        "猫咪柔紫", "1E1E2E", "313244", "CDD6F4", "A6ADC8",
        "CBA6F7", "89B4FA", "45475A", dark=True,
        series=["CBA6F7", "89B4FA", "94E2D5", "F9E2AF", "F38BA8"],
    ),
    "terminal_green": _theme(
        "终端荧光", "090C0A", "111713", "E7FBEA", "7D9A83",
        "39FF88", "B4FF39", "25352A", mono="SF Mono", dark=True,
        series=["39FF88", "B4FF39", "37D5D3", "F7C948", "F56C6C"],
    ),
    "cobalt_tech": _theme(
        "钴蓝科技", "071A33", "0D2748", "F2F7FF", "A7BAD0",
        "2D7FF9", "67E8F9", "214467", dark=True,
        series=["2D7FF9", "67E8F9", "6EE7B7", "FBBF24", "F472B6"],
    ),

    # Research and data journalism
    "academic_navy": _theme(
        "学术海军蓝", "F8FAFC", "FFFFFF", "17223B", "64748B",
        "1F4E79", "A44A3F", "D8E1EA", heading="Songti SC",
        series=["1F4E79", "A44A3F", "5E8C6A", "D4A72C", "7A6FA8"],
    ),
    "data_journalism": _theme(
        "数据新闻", "FBFAF7", "FFFFFF", "242424", "6D6D6D",
        "176B87", "D65A31", "DEDAD2", heading="Songti SC",
        series=["176B87", "D65A31", "5B8C5A", "D3A32A", "7E6AB4"],
    ),
    "arctic_frost": _theme(
        "北极霜蓝", "F3F8FC", "FFFFFF", "20354A", "6B7F92",
        "4A6FA5", "69B7C6", "D8E5EE",
        series=["4A6FA5", "69B7C6", "7A9E9F", "A3B8CC", "C4D7E5"],
    ),
    "cherry_bold": _theme(
        "樱桃高对比", "FCF6F5", "FFFFFF", "2D2525", "7D6B6B",
        "990011", "2F3C7E", "E8DAD8",
        series=["990011", "2F3C7E", "C55A6A", "7783B5", "C9A0A5"],
    ),
}


ALIASES = {
    "地产黑金": "realestate_gold", "高管深蓝": "executive_navy", "金融墨绿": "financial_green",
    "建筑沙丘": "architectural_sand", "瑞士墨水": "swiss_monocle", "编辑部墨黑": "editorial_ink",
    "暖沙陶土": "terracotta_warm", "森林墨绿": "forest_canopy", "金秋夕照": "autumn_amber",
    "极简纯白": "vercel_minimal", "苹果发布会": "apple_keynote", "新粗野纯白": "brutalist_white",
    "包豪斯原色": "bauhaus_primary", "柔雾粉彩": "soft_pastel", "午夜蓝黑": "midnight_executive",
    "赛博深光": "cyber_neocarbon", "猫咪柔紫": "catppuccin_mauve", "终端荧光": "terminal_green",
    "钴蓝科技": "cobalt_tech", "学术海军蓝": "academic_navy", "数据新闻": "data_journalism",
    "北极霜蓝": "arctic_frost", "樱桃高对比": "cherry_bold",
}


def get_theme(name):
    return THEMES.get(ALIASES.get(name, name), THEMES["vercel_minimal"])

"""
Japanese → English value normalizers and lookup maps.
"""

from __future__ import annotations

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Numeric normalizers
# ---------------------------------------------------------------------------

def normalize_year(raw: str) -> Optional[int]:
    m = re.search(r"(\d{4})", raw or "")
    return int(m.group(1)) if m else None


def normalize_mileage_km(raw: str) -> Optional[int]:
    raw = (raw or "").replace(",", "").replace("，", "")
    m_man = re.search(r"([\d.]+)\s*万\s*km", raw)
    if m_man:
        return int(round(float(m_man.group(1)) * 10_000))
    m_plain = re.search(r"([\d.]+)\s*km", raw)
    if m_plain:
        return int(round(float(m_plain.group(1))))
    return None


def normalize_price_jpy(raw: str) -> Optional[int]:
    raw = (raw or "").replace(",", "").replace("，", "")
    m_man = re.search(r"([\d.]+)\s*万\s*円", raw)
    if m_man:
        return int(round(float(m_man.group(1)) * 10_000))
    m_plain = re.search(r"([\d]+)\s*円", raw)
    if m_plain:
        return int(m_plain.group(1))
    m_num = re.search(r"^([\d]+)$", raw.strip())
    if m_num:
        return int(m_num.group(1))
    return None


# ---------------------------------------------------------------------------
# Lookup maps
# ---------------------------------------------------------------------------

BRAND_MAP: dict[str, str] = {
    # Japanese domestic
    "トヨタ": "Toyota", "ホンダ": "Honda", "日産": "Nissan",
    "スバル": "Subaru", "マツダ": "Mazda", "三菱": "Mitsubishi",
    "スズキ": "Suzuki", "ダイハツ": "Daihatsu", "いすゞ": "Isuzu",
    "レクサス": "Lexus", "インフィニティ": "Infiniti", "アキュラ": "Acura",
    # German
    "メルセデス・ベンツ": "Mercedes-Benz", "メルセデスベンツ": "Mercedes-Benz",
    "BMW": "BMW", "アウディ": "Audi", "フォルクスワーゲン": "Volkswagen",
    "ポルシェ": "Porsche", "スマート": "Smart", "オペル": "Opel",
    # Italian
    "フィアット": "Fiat", "フェラーリ": "Ferrari", "ランボルギーニ": "Lamborghini",
    "マセラティ": "Maserati", "アルファ　ロメオ": "Alfa Romeo", "アルファロメオ": "Alfa Romeo",
    "アバルト": "Abarth", "ランチア": "Lancia",
    # British
    "ジャガー": "Jaguar", "ランドローバー": "Land Rover", "ミニ": "MINI",
    "ベントレー": "Bentley", "ロールスロイス": "Rolls-Royce", "マクラーレン": "McLaren",
    "ロータス": "Lotus", "アストンマーティン": "Aston Martin",
    # American
    "フォード": "Ford", "シボレー": "Chevrolet", "キャデラック": "Cadillac",
    "クライスラー": "Chrysler", "ジープ": "Jeep", "ダッジ": "Dodge",
    "リンカーン": "Lincoln", "ハマー": "Hummer", "テスラ": "Tesla",
    # French
    "プジョー": "Peugeot", "シトロエン": "Citroën", "ルノー": "Renault",
    # Swedish / Other
    "ボルボ": "Volvo", "サーブ": "Saab", "ヒュンダイ": "Hyundai", "キア": "Kia",
}

MODEL_MAP: dict[str, str] = {
    # Alfa Romeo
    "ジュリア": "Giulia", "ジュリエッタ": "Giulietta", "ステルヴィオ": "Stelvio",
    "ミト": "MiTo", "スパイダー": "Spider", "ブレラ": "Brera",
    # Audi
    "クワトロ": "Quattro",
    # BMW
    "グランクーペ": "Gran Coupe", "グランツーリスモ": "Gran Turismo",
    "2シリーズグランツアラー": "2 Series Gran Tourer",
    "2シリーズアクティブツアラー": "2 Series Active Tourer",
    "3シリーズツーリング": "3 Series Touring",
    # Ferrari
    "カリフォルニア": "California", "ポルトフィーノ": "Portofino",
    "ローマ": "Roma", "テスタロッサ": "Testarossa",
    # Lamborghini
    "ウラカン": "Huracán", "アヴェンタドール": "Aventador", "ウルス": "Urus",
    # Maserati
    "クワトロポルテ": "Quattroporte", "ギブリ": "Ghibli", "グランカブリオ": "GranCabrio",
    "グランツーリスモ": "GranTurismo", "レヴァンテ": "Levante",
    # Mercedes-Benz
    "マイバッハ": "Maybach",
    "Cクラス": "C-Class", "Cクラスワゴン": "C-Class Wagon",
    "Eクラス": "E-Class", "Aクラスセダン": "A-Class Sedan",
    "Aクラス": "A-Class", "Bクラス": "B-Class",
    "CLAクラス": "CLA-Class",
    "A7スポーツバック": "A7 Sportback",
    "A3スポーツバック": "A3 Sportback", "A3セダン": "A3 Sedan",
    "A1スポーツバック": "A1 Sportback",
    # Porsche
    "カイエン": "Cayenne", "マカン": "Macan", "パナメーラ": "Panamera",
    "タイカン": "Taycan", "ボクスター": "Boxster", "ケイマン": "Cayman",
    # Rolls-Royce
    "ファントム": "Phantom", "レイス": "Wraith", "ゴースト": "Ghost",
    "カリナン": "Cullinan", "ドーン": "Dawn",
    # Bentley
    "コンチネンタル": "Continental", "フライングスパー": "Flying Spur",
    "ベンテイガ": "Bentayga", "ミュルザンヌ": "Mulsanne",
    # Toyota
    "プリウス": "Prius", "クラウン": "Crown", "カムリ": "Camry",
    "クラウンロイヤル": "Crown Royal",
    "ランドクルーザー": "Land Cruiser", "ランドクルーザープラド": "Land Cruiser Prado",
    "ハイエース": "Hiace", "ハイエースバン": "Hiace Van",
    "アルファード": "Alphard",
    "ヴェルファイア": "Vellfire", "ハリアー": "Harrier", "ヴォクシー": "Voxy",
    "シエンタ": "Sienta", "ヤリス": "Yaris", "アクア": "Aqua",
    "ノア": "Noah", "エスティマ": "Estima", "セルシオ": "Celsior",
    "スープラ": "Supra", "86": "86", "GR86": "GR86",
    "カローラツーリング": "Corolla Touring", "カローラクロス": "Corolla Cross",
    "カローラフィールダー": "Corolla Fielder", "カローラアクシオ": "Corolla Axio",
    "ヴィッツ": "Vitz", "ライズ": "Raize",
    "スペイド": "Spade", "エスクァイア": "Esquire",
    "プリウスα": "Prius α", "プリウスPHV": "Prius PHV",
    "マークX": "Mark X",
    # Honda
    "フィット": "Fit", "シビック": "Civic", "アコード": "Accord",
    "ステップワゴン": "Step WGN", "フリード": "Freed", "ヴェゼル": "Vezel",
    "エヌボックス": "N-BOX", "オデッセイ": "Odyssey", "レジェンド": "Legend",
    # Nissan
    "スカイライン": "Skyline", "フェアレディＺ": "Fairlady Z", "フェアレディZ": "Fairlady Z",
    "ノート": "Note", "ノートオーラ": "Note Aura",
    "セレナ": "Serena", "エクストレイル": "X-Trail",
    "ジューク": "Juke", "キャラバン": "Caravan", "エルグランド": "Elgrand",
    "ルークス": "Roox", "デイズ": "Dayz",
    "NV200バネットバン": "NV200 Vanette Van",
    "フーガ": "Fuga", "フーガハイブリッド": "Fuga Hybrid",
    "ティアナ": "Teana", "リーフ": "Leaf",
    # Lexus
    "GSハイブリッド": "GS Hybrid",
    # Subaru
    "インプレッサ": "Impreza", "インプレッサスポーツ": "Impreza Sport",
    "インプレッサG4": "Impreza G4", "インプレッサハッチバック": "Impreza Hatchback",
    "レガシィ": "Legacy", "フォレスター": "Forester",
    "アウトバック": "Outback", "レヴォーグ": "Levorg",
    "レヴォーグレイバック": "Levorg Layback", "BRZ": "BRZ",
    "エクシーガクロスオーバー7": "Exiga Crossover 7",
    # Mazda
    "デミオ": "Demio", "アテンザ": "Atenza", "アクセラ": "Axela",
    "アクセラスポーツ": "Axela Sport",
    "MAZDA3ファストバック": "MAZDA3 Fastback", "MAZDA3セダン": "MAZDA3 Sedan",
    "ＣＸ－５": "CX-5", "CX-5": "CX-5", "ＣＸ－３": "CX-3", "ロードスター": "Roadster",
    # Mitsubishi
    "アウトランダー": "Outlander", "エクリプスクロス": "Eclipse Cross",
    "パジェロ": "Pajero", "デリカ": "Delica",
    "デリカD：2": "Delica D:2", "デリカD:2": "Delica D:2", "デリカミニ": "Delica Mini",
    "eKスペース": "eK Space", "eKワゴン": "eK Wagon",
    "eKクロス": "eK Cross", "eKクロススペース": "eK Cross Space",
    # Suzuki
    "ジムニー": "Jimny", "ジムニーノマド": "Jimny Nomad",
    "スイフト": "Swift", "ソリオ": "Solio",
    "ハスラー": "Hustler", "アルト": "Alto", "アルトラパン": "Alto Lapin",
    "ワゴンＲ": "Wagon R", "ワゴンR": "Wagon R", "ワゴンRスマイル": "Wagon R Smile",
    "スペーシア": "Spacia", "クロスビー": "Crossbe",
    "イグニス": "Ignis", "エスクード": "Escudo",
    # Daihatsu
    "ミラ": "Mira", "ミライース": "Mira e:S", "ミラトコット": "Mira Tocot",
    "タント": "Tanto", "タフト": "Taft",
    "ムーヴ": "Move", "ムーヴキャンバス": "Move Canbus",
    "コペン": "Copen", "キャスト": "Cast",
    "ピクシスメガ": "Pixis Mega",
    # Jeep (via Chrysler/FCA group, sold in Japan)
    "グランドチェロキー": "Grand Cherokee",
    # Volkswagen
    "ゴルフ": "Golf",
    # Renault
    "メガーヌ": "Mégane", "ラフェスタハイウェイスター": "LaFesta Highway Star",
    # smart
    "フォーフォー": "Forfour",
    # MINI
    "ミニクラブマン": "MINI Clubman",
    # Honda (kei)
    "エブリイワゴン": "Every Wagon",
}

COLOR_MAP: dict[str, str] = {
    "ブラック": "Black", "黒": "Black",
    "ホワイト": "White", "白": "White",
    "シルバー": "Silver", "シルバーメタリック": "Silver",
    "グレー": "Gray", "グレイ": "Gray", "灰": "Gray",
    "レッド": "Red", "赤": "Red",
    "ブルー": "Blue", "青": "Blue",
    "ネイビー": "Navy",
    "グリーン": "Green", "緑": "Green",
    "ゴールド": "Gold", "金": "Gold",
    "ブラウン": "Brown", "茶": "Brown",
    "ベージュ": "Beige",
    "オレンジ": "Orange",
    "イエロー": "Yellow", "黄": "Yellow",
    "パープル": "Purple", "紫": "Purple",
    "ピンク": "Pink",
    "ワインレッド": "Wine Red", "バーガンディ": "Burgundy",
    "チャンパン": "Champagne",
    # compound / pearl / metallic variants
    "ホワイトパールクリスタルシャイン": "Pearl White",
    "クリスタルブラックパール": "Pearl Black",
    "グラファイトブラックガラスフレーク": "Graphite Black",
    "アイスホワイト": "Ice White",
    "パール": "Pearl White",
    "ミモザイエローパールメタリック": "Yellow Pearl",
    "ソニックシルバー": "Silver",
    "ソニックチタニウム": "Sonic Titanium",
    "パールマイカ": "Pearl",
    "マスタードイエローマイカメタリック": "Mustard Yellow",
    "マスタード": "Mustard",
    "ブリリアントホワイトパール": "Brilliant White Pearl",
    "ブリリアントブロンズ・メタリック": "Brilliant Bronze Metallic",
    "アッシュ": "Ash Gray",
    "ムーンライトブルーパールメタリック": "Blue Pearl",
    "ダークグレーメタリック": "Dark Gray",
    "ダークバイオレットマイカメタリック": "Dark Violet Mica Metallic",
    "プレミアムホワイトパールクリスタルシャイン": "Pearl White",
    "スーパープラチナ・メタリック": "Super Platinum Metallic",
    "プラチナクォーツメタリック": "Platinum Quartz Metallic",
    "プレシャスメタル": "Precious Metal",
    "テレーンカーキマイカメタリック": "Terrain Khaki Mica Metallic",
    "シフォンアイボリーメタリック": "Chiffon Ivory Metallic",
    "スティールブロンドメタリック": "Steel Blonde Metallic",
    "オフビートカーキメタリック": "Off-Beat Khaki Metallic",
    "ライトローズマイカメタリック": "Light Rose Mica Metallic",
    "キュイーヴルソラール": "Cuivre Solaire",
    "ガンメタリック": "Gun Metallic",
    "レモンライム": "Lemon Lime",
    "ビアンコ ガーラ": "Bianco Gala",
}

TRANSMISSION_MAP: dict[str, str] = {
    "フロアMTモード付CVT": "CVT", "CVT": "CVT", "セミAT": "Semi-AT",
    "デュアルクラッチ": "DCT", "2ペダルMT": "2-pedal MT", "AT": "AT", "MT": "MT",
}

FUEL_MAP: dict[str, str] = {
    "ガソリン": "gasoline", "ディーゼル": "diesel", "ハイブリッド": "hybrid",
    "電気": "electric", "プラグインハイブリッド": "PHEV", "水素": "hydrogen", "LPG": "LPG",
}

BODY_MAP: dict[str, str] = {
    "ステーションワゴン": "station wagon", "ミニバン/ワンボックス": "minivan",
    "SUV/クロカン": "SUV", "クロカン・ＳＵＶ": "SUV", "クロカン": "SUV",
    "軽トラック/軽バン": "kei truck/van",
    "セダン": "sedan", "ハッチバック": "hatchback", "コンパクト": "compact",
    "ミニバン": "minivan", "SUV": "SUV", "クーペ": "coupe",
    "オープンカー": "convertible", "軽自動車": "kei car",
    "トラック/バン": "truck/van", "バス": "bus",
}


# ---------------------------------------------------------------------------
# Mapper functions
# ---------------------------------------------------------------------------

def map_brand(ja: str) -> str:
    return BRAND_MAP.get(ja.strip(), ja.strip())


def map_model(ja: str) -> str:
    return MODEL_MAP.get(ja.strip(), ja.strip())


def map_transmission(ja: str) -> str:
    for k in sorted(TRANSMISSION_MAP, key=len, reverse=True):
        if k in ja:
            return TRANSMISSION_MAP[k]
    return ja.strip()


def map_fuel(ja: str) -> str:
    return FUEL_MAP.get(ja.strip(), ja.strip())


def map_body(ja: str) -> str:
    for k, v in BODY_MAP.items():
        if k in ja:
            return v
    return ja.strip()


def map_color(ja: str) -> str:
    """Translate Japanese color string to English. Tries longest match first."""
    ja = ja.strip()
    if ja in COLOR_MAP:
        return COLOR_MAP[ja]
    for k in sorted(COLOR_MAP, key=len, reverse=True):
        if k in ja:
            return COLOR_MAP[k]
    return ja

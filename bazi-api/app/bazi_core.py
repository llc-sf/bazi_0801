# -*- encoding:utf-8 -*- 

import sxtwl, json
from datetime import datetime, timedelta
# import ephem
from math import radians, sin, cos
import math 

# 基础表
TG  = "甲乙丙丁戊己庚辛壬癸"
DZ  = "子丑寅卯辰巳午未申酉戌亥"
ELE = dict(zip(TG, "木木火火土土金金水水"))

# 地支五行属性
DZ_ELE = dict(zip(DZ, "水土木木土火火土金金土水"))

# 地支藏干（主气）
DZ_CANG_GAN = {
    "子": "癸", "丑": "己", "寅": "甲", "卯": "乙", 
    "辰": "戊", "巳": "丙", "午": "丁", "未": "己",
    "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬"
}

# 十神名称
SHEN = ["比肩","劫财","食神","伤官","偏财","正财","七杀","正官","偏印","正印"]

# 天干阴阳属性 (True为阳，False为阴)
YIN_YANG = dict(zip(TG, [True, False, True, False, True, False, True, False, True, False]))

# 地支阴阳属性 (True为阳，False为阴)
# 子寅辰午申戌为阳，丑卯巳未酉亥为阴
DZ_YIN_YANG = dict(zip(DZ, [True, False, True, False, True, False, True, False, True, False, True, False]))

# 五行生克关系
WU_XING_SHENG = {
    "木": "火",  # 木生火
    "火": "土",  # 火生土  
    "土": "金",  # 土生金
    "金": "水",  # 金生水
    "水": "木"   # 水生木
}

WU_XING_KE = {
    "木": "土",  # 木克土
    "火": "金",  # 火克金
    "土": "水",  # 土克水
    "金": "木",  # 金克木
    "水": "火"   # 水克火
}

#TG = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
#DZ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

from datetime import datetime

# 1. 预置城市数据库（部分示例）
# city_coordinates = {"北京": (116.40, 39.90), "上海": (121.47, 31.23)}
def parse_city_coordinates(file_path: str) -> dict:
    """
    从文件解析城市经纬度数据，生成{city_name: (lng, lat)}字典
    文件格式：编码 省份城市 经度 纬度（空格/tab分隔）
    """
    city_coordinates = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # 分割字段（兼容空格/tab混合）
            parts = line.strip().split()
            if len(parts) < 4:
                continue  # 跳过格式错误行
            
            # 解析字段
            code = parts[0]
            name = parts[1]
            try:
                lng = float(parts[2])
                lat = float(parts[3])
            except ValueError:
                continue  # 跳过数值错误行
            
            # 主键：使用完整城市名称
            city_coordinates[name] = (lng, lat)
            
            # 添加简化名称支持（去掉"市"、"省"、"自治区"等后缀）
            simplified_name = name
            for suffix in ['市', '省', '自治区', '特别行政区', '县', '区']:
                if simplified_name.endswith(suffix):
                    simplified_name = simplified_name[:-len(suffix)]
                    city_coordinates[simplified_name] = (lng, lat)
                    break
    
    return city_coordinates

def calculate_eot(date: datetime) -> float:
    """计算时差修正值(EoT) - 单位：分钟"""
    n = date.timetuple().tm_yday  # 年内天数
    b = math.radians((n - 81) * 360 / 365.242)
    # 椭圆轨道修正公式
    eot = 9.87 * math.sin(2*b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    return eot

city_coordinates = parse_city_coordinates("/app/app/data.txt")
# 2. 真太阳时计算函数
def true_solar_time(city_name: str, local_dt: datetime) -> datetime:
    # 尝试精确匹配
    coordinates = city_coordinates.get(city_name)
    
    if not coordinates:
        # 尝试模糊匹配（在城市名称中搜索）
        for city, coord in city_coordinates.items():
            if city_name in city or city in city_name:
                coordinates = coord
                break
    
    if not coordinates:
        # 提供可用城市的提示
        available_cities = [city for city in city_coordinates.keys() if len(city) <= 10][:10]
        raise ValueError(f"城市 '{city_name}' 经纬度未收录。可用城市示例：{', '.join(available_cities[:5])}等")
    
    lon, lat = coordinates
    
    # 2. 计算经度时差（120°为东八区基准）
    lon_diff = (120 - lon) * 4  # 单位：分钟
    
    # 3. 计算时差修正值(EoT)
    eot = calculate_eot(local_dt)
    
    # 4. 计算真太阳时
    total_correction = timedelta(minutes=(lon_diff + eot))
    return local_dt + total_correction


def gan_idx(g): return TG.index(g)

def ten_shen(day_gan, target_gan):
    """
    根据日干和目标天干计算十神关系
    
    Args:
        day_gan: 日干（如：甲、乙、丙等）
        target_gan: 目标天干（年干、月干、时干等）
        
    Returns:
        十神名称（如：比肩、劫财、食神等）
    """
    # 获取五行属性
    day_ele = ELE[day_gan]
    target_ele = ELE[target_gan]
    
    # 获取阴阳属性
    day_yin_yang = YIN_YANG[day_gan]
    target_yin_yang = YIN_YANG[target_gan]
    
    # 判断是否同性（同为阳或同为阴）
    is_same_yin_yang = day_yin_yang == target_yin_yang
    
    # 1. 同类关系（相同五行）
    if day_ele == target_ele:
        if day_gan == target_gan:
            return "比肩"  # 完全相同
        elif is_same_yin_yang:
            return "劫财"  # 同类同性
        else:
            return "比肩"  # 同类异性
    
    # 2. 日干生目标干（食伤）
    elif WU_XING_SHENG.get(day_ele) == target_ele:
        if is_same_yin_yang:
            return "食神"  # 日干生同性
        else:
            return "伤官"  # 日干生异性
    
    # 3. 日干克目标干（财星）  
    elif WU_XING_KE.get(day_ele) == target_ele:
        if is_same_yin_yang:
            return "偏财"  # 日干克同性
        else:
            return "正财"  # 日干克异性
    
    # 4. 目标干生日干（印星）
    elif WU_XING_SHENG.get(target_ele) == day_ele:
        if is_same_yin_yang:
            return "偏印"  # 同性生日干
        else:
            return "正印"  # 异性生日干
    
    # 5. 目标干克日干（官杀）
    elif WU_XING_KE.get(target_ele) == day_ele:
        if is_same_yin_yang:
            return "七杀"  # 同性克日干
        else:
            return "正官"  # 异性克日干
    
    # 默认返回（理论上不应该到达这里）
    return "未知"


def ten_shen_dz(day_gan, target_dz):
    """
    根据日干和目标地支计算十神关系（基于地支藏干主气）
    
    Args:
        day_gan: 日干（如：甲、乙、丙等）
        target_dz: 目标地支（如：子、丑、寅等）
        
    Returns:
        十神名称（如：比肩、劫财、食神等）
    """
    # 获取地支藏干主气
    target_gan = DZ_CANG_GAN[target_dz]
    
    # 使用藏干主气计算十神
    return ten_shen(day_gan, target_gan)


def calc_bazi(name, city, gender, year, month, day, hour, minute=0):

    # 1. 北京时 -> 当地标准时
    local_dt = datetime(year, month, day, hour, minute)
    # 2. 当地标准时 -> 真太阳时
    true_dt = true_solar_time(city, local_dt)

    # 3. 八字

    day_obj = sxtwl.fromSolar(year, month, day) 

    # 公历 → 农历
    # 农历日期
    lunar_year  = day_obj.getLunarYear()
    lunar_month = day_obj.getLunarMonth()
    lunar_day   = day_obj.getLunarDay()
    is_leap     = bool(day_obj.isLunarLeap())

    d = sxtwl.fromSolar(true_dt.year, true_dt.month, true_dt.day)
    d = sxtwl.fromSolar(year, month, day)

    # 农历日期
    lunar_year  = d.getLunarYear()
    lunar_month = d.getLunarMonth()
    lunar_day   = d.getLunarDay()
    is_leap     = bool(d.isLunarLeap())

    yg, mg, dg, hg = TG[d.getYearGZ().tg] + DZ[d.getYearGZ().dz], TG[d.getMonthGZ().tg] + DZ[d.getMonthGZ().dz], \
                     TG[d.getDayGZ().tg] + DZ[d.getDayGZ().dz], TG[d.getHourGZ(hour).tg] + DZ[d.getHourGZ(hour).dz]


    return {
        "姓名": name,
        "城市": city,
        "北京时": local_dt.strftime("%Y-%m-%d %H:%M"),
        "真太阳时": true_dt.strftime("%Y-%m-%d %H:%M"),
        "农历": f"{lunar_year}年{'闰' if is_leap else ''}{lunar_month}月{lunar_day}日",
        "八字": f"{yg} {mg} {dg} {hg}",
        "五行": " ".join([f"{g}({ELE[g]})" for g in (yg[0], mg[0], dg[0], hg[0])]),
        "十神": {
            "年干": ten_shen(dg[0], yg[0]),
            "年支": ten_shen_dz(dg[0], yg[1]),
            "月干": ten_shen(dg[0], mg[0]),
            "月支": ten_shen_dz(dg[0], mg[1]),
            "日干": "元男" if gender == "男" else "元女",
            "日支": ten_shen_dz(dg[0], dg[1]),
            "时干": ten_shen(dg[0], hg[0]),
            "时支": ten_shen_dz(dg[0], hg[1])
        }
    }

def get_next_gan_zhi(gan_zhi, direction=1):
    """
    获取下一个干支组合
    
    Args:
        gan_zhi: 当前干支（如：甲子）
        direction: 方向（1为顺，-1为逆）
    
    Returns:
        下一个干支
    """
    gan = gan_zhi[0]
    zhi = gan_zhi[1]
    
    gan_idx = TG.index(gan)
    zhi_idx = DZ.index(zhi)
    
    # 计算下一个干支
    next_gan_idx = (gan_idx + direction) % 10
    next_zhi_idx = (zhi_idx + direction) % 12
    
    return TG[next_gan_idx] + DZ[next_zhi_idx]


def calc_da_yun(birth_year, month_gan_zhi, day_gan, gender):
    """
    计算大运
    
    Args:
        birth_year: 出生年份
        month_gan_zhi: 月柱干支
        day_gan: 日干
        gender: 性别
    
    Returns:
        大运列表
    """
    # 判断年干阴阳
    year_gan = TG[(birth_year - 4) % 10]  # 天干纪年算法
    is_yang_year = YIN_YANG[year_gan]  # True为阳年，False为阴年
    
    # 确定排运方向
    if (is_yang_year and gender == "男") or (not is_yang_year and gender == "女"):
        direction = 1  # 顺排
    else:
        direction = -1  # 逆排
    
    # 简化起运年龄计算（实际应该根据节气计算，这里用固定值）
    start_age = 8  # 暂定8岁起运
    
    # 计算10步大运
    da_yun = []
    current_gan_zhi = month_gan_zhi
    
    for i in range(10):
        if i == 0:
            # 第一步大运从月柱开始计算
            current_gan_zhi = get_next_gan_zhi(month_gan_zhi, direction)
        else:
            current_gan_zhi = get_next_gan_zhi(current_gan_zhi, direction)
        
        start_year = start_age + i * 10
        end_year = start_year + 9
        
        da_yun.append({
            "干支": current_gan_zhi,
            "起止年龄": f"{start_year}-{end_year}岁",
            "十神干": ten_shen(day_gan, current_gan_zhi[0]),
            "十神支": ten_shen_dz(day_gan, current_gan_zhi[1])
        })
    
    return {
        "排运方式": "顺排" if direction == 1 else "逆排",
        "起运年龄": f"{start_age}岁",
        "大运": da_yun
    }


def calc_bazi(name, city, gender, year, month, day, hour, minute=0):

    # 1. 北京时 -> 当地标准时
    local_dt = datetime(year, month, day, hour, minute)
    # 2. 当地标准时 -> 真太阳时
    true_dt = true_solar_time(city, local_dt)

    # 3. 八字

    day_obj = sxtwl.fromSolar(year, month, day) 

    # 公历 → 农历
    # 农历日期
    lunar_year  = day_obj.getLunarYear()
    lunar_month = day_obj.getLunarMonth()
    lunar_day   = day_obj.getLunarDay()
    is_leap     = bool(day_obj.isLunarLeap())

    d = sxtwl.fromSolar(true_dt.year, true_dt.month, true_dt.day)
    d = sxtwl.fromSolar(year, month, day)

    # 农历日期
    lunar_year  = d.getLunarYear()
    lunar_month = d.getLunarMonth()
    lunar_day   = d.getLunarDay()
    is_leap     = bool(d.isLunarLeap())

    yg, mg, dg, hg = TG[d.getYearGZ().tg] + DZ[d.getYearGZ().dz], TG[d.getMonthGZ().tg] + DZ[d.getMonthGZ().dz], \
                     TG[d.getDayGZ().tg] + DZ[d.getDayGZ().dz], TG[d.getHourGZ(hour).tg] + DZ[d.getHourGZ(hour).dz]

    # 计算大运
    da_yun_info = calc_da_yun(year, mg, dg[0], gender)

    return {
        "姓名": name,
        "城市": city,
        "北京时": local_dt.strftime("%Y-%m-%d %H:%M"),
        "真太阳时": true_dt.strftime("%Y-%m-%d %H:%M"),
        "农历": f"{lunar_year}年{'闰' if is_leap else ''}{lunar_month}月{lunar_day}日",
        "八字": f"{yg} {mg} {dg} {hg}",
        "五行": " ".join([f"{g}({ELE[g]})" for g in (yg[0], mg[0], dg[0], hg[0])]),
        "十神": {
            "年干": ten_shen(dg[0], yg[0]),
            "年支": ten_shen_dz(dg[0], yg[1]),
            "月干": ten_shen(dg[0], mg[0]),
            "月支": ten_shen_dz(dg[0], mg[1]),
            "日干": "元男" if gender == "男" else "元女",
            "日支": ten_shen_dz(dg[0], dg[1]),
            "时干": ten_shen(dg[0], hg[0]),
            "时支": ten_shen_dz(dg[0], hg[1])
        },
        "大运": da_yun_info
    }

def solar_to_bazi(name: str, city: str, gender: str, year: int, month: int, day: int, hour: int, minute: int = 0):

    json_data = {}
    try:
        json_data = calc_bazi(name, city, gender, year, month, day, hour, minute)
    except Exception as e:
        print(e)

    return json.dumps(json_data, ensure_ascii=False, indent=2)

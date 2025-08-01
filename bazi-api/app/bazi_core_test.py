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
SHEN = ["比肩","劫财","食神","伤官","偏财","正财","七杀","正官","偏印","正印"]
#TG = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
#DZ = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

from datetime import datetime

# 1. 预置城市数据库（部分示例）
# city_coordinates = {"北京": (116.40, 39.90), "上海": (121.47, 31.23)}
def parse_city_coordinates(file_path="./data.txt": str) -> dict:
    """
    从文件解析城市经纬度数据，生成{city_name: (lng, lat)}字典
    文件格式：编码 省份城市 经度 纬度（空格/tab分隔）
    """
    city_coordinates = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        # 跳过标题行
        next(file)  
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
            
            # 主键：使用城市名称
            city_coordinates[name] = (lng, lat)
            
            # 可选：添加带省前缀的键（如"北京-北京市"）
            if '省' in name or '市' in name:
                province_city = name[:-1] + '-' + name  # 示例：北京-北京市
                city_coordinates[province_city] = (lng, lat)
    
    return city_coordinates

def calculate_eot(date: datetime) -> float:
    """计算时差修正值(EoT) - 单位：分钟"""
    n = date.timetuple().tm_yday  # 年内天数
    b = math.radians((n - 81) * 360 / 365.242)
    # 椭圆轨道修正公式
    eot = 9.87 * math.sin(2*b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
    return eot

city_coordinates = parse_city_coordinates("./data.txt")
# 2. 真太阳时计算函数
def true_solar_time(city_name: str, local_dt: datetime) -> datetime:
    lon, lat = city_coordinates.get(city_name, (None, None))
    if not lon:
        raise ValueError(f"城市 '{city_name}' 经纬度未收录")
    
    # 2. 计算经度时差（120°为东八区基准）
    lon_diff = (120 - lon) * 4  # 单位：分钟
    
    # 3. 计算时差修正值(EoT)
    eot = calculate_eot(local_dt)
    
    # 4. 计算真太阳时
    total_correction = timedelta(minutes=(lon_diff + eot))
    return local_dt + total_correction


def gan_idx(g): return TG.index(g)
def ten_shen(day_gan, gan): return SHEN[(gan_idx(gan) - gan_idx(day_gan)) % 10]


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
            "年柱": ten_shen(dg[0], yg[0]),
            "月柱": ten_shen(dg[0], mg[0]),
            "日柱": "元男" if gender == "男" else "元女",
            "时柱": ten_shen(dg[0], hg[0])
        }
    }

def solar_to_bazi(name: str, city: str, gender: str, year: int, month: int, day: int, hour: int, minute: int = 0):

    json_data = {}
    try:
        json_data = calc_bazi(name, city, gender, year, month, day, hour, minute)
    except Exception as e:
        print(e)

    return json.dumps(json_data, ensure_ascii=False, indent=2)

if __name__=='__main__':
    print(solar_to_bazi("令狐冲", "北京市","男", 1999, 2,13,12,0))
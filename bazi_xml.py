#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: 钉钉或微信pythontesting 钉钉群21734177
# CreateDate: 2024-01-01

import argparse
import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

from lunar_python import Lunar, Solar
from datas import *
from common import *
from ganzhi import *
from yue import months

def create_bazi_xml(name, birthplace, year, month, day, time, is_female=False, is_lunar=False):
    """
    生成八字分析的XML格式数据
    
    Args:
        name: 姓名
        birthplace: 出生地
        year: 出生年份
        month: 出生月份
        day: 出生日
        time: 出生时辰
        is_female: 是否女性
        is_lunar: 是否农历
    
    Returns:
        XML格式的字符串
    """
    
    # 创建根元素
    root = ET.Element("八字分析")
    
    # 基本信息
    info = ET.SubElement(root, "基本信息")
    ET.SubElement(info, "姓名").text = name
    ET.SubElement(info, "出生地").text = birthplace
    ET.SubElement(info, "性别").text = "女" if is_female else "男"
    
    # 计算八字
    if is_lunar:
        lunar = Lunar.fromYmd(year, month, day)
        solar = lunar.getSolar()
    else:
        solar = Solar.fromYmd(year, month, day)
        lunar = Solar.fromYmd(year, month, day).getLunar()
    
    ba = lunar.getEightChar()
    gans = collections.namedtuple('gans', ['year', 'month', 'day', 'time'])(
        ba.getYearGan(), ba.getMonthGan(), ba.getDayGan(), ba.getTimeGan(time)
    )
    zhis = collections.namedtuple('zhis', ['year', 'month', 'day', 'time'])(
        ba.getYearZhi(), ba.getMonthZhi(), ba.getDayZhi(), ba.getTimeZhi(time)
    )
    
    # 时间信息
    time_info = ET.SubElement(info, "时间信息")
    ET.SubElement(time_info, "公历").text = f"{solar.getYear()}年{solar.getMonth()}月{solar.getDay()}日"
    ET.SubElement(time_info, "农历").text = f"{lunar.getYear()}年{lunar.getMonth()}月{lunar.getDay()}日"
    ET.SubElement(time_info, "出生时辰").text = f"{time}时 ({zhi_time.get(zhis.time, time)})"
    
    # 八字信息
    bazi = ET.SubElement(root, "八字信息")
    
    # 四柱
    sizhu = ET.SubElement(bazi, "四柱")
    
    # 年柱
    nianzhu = ET.SubElement(sizhu, "年柱")
    ET.SubElement(nianzhu, "天干").text = gans.year
    ET.SubElement(nianzhu, "地支").text = zhis.year
    ET.SubElement(nianzhu, "五行").text = f"{gan5[gans.year]}{zhi_wuhangs[zhis.year]}"
    ET.SubElement(nianzhu, "纳音").text = nayins.get((gans.year, zhis.year), "")
    
    # 月柱
    yuezhu = ET.SubElement(sizhu, "月柱")
    ET.SubElement(yuezhu, "天干").text = gans.month
    ET.SubElement(yuezhu, "地支").text = zhis.month
    ET.SubElement(yuezhu, "五行").text = f"{gan5[gans.month]}{zhi_wuhangs[zhis.month]}"
    ET.SubElement(yuezhu, "纳音").text = nayins.get((gans.month, zhis.month), "")
    
    # 日柱
    rizhu = ET.SubElement(sizhu, "日柱")
    ET.SubElement(rizhu, "天干").text = gans.day
    ET.SubElement(rizhu, "地支").text = zhis.day
    ET.SubElement(rizhu, "五行").text = f"{gan5[gans.day]}{zhi_wuhangs[zhis.day]}"
    ET.SubElement(rizhu, "纳音").text = nayins.get((gans.day, zhis.day), "")
    ET.SubElement(rizhu, "日主").text = gans.day
    
    # 时柱
    shizhu = ET.SubElement(sizhu, "时柱")
    ET.SubElement(shizhu, "天干").text = gans.time
    ET.SubElement(shizhu, "地支").text = zhis.time
    ET.SubElement(shizhu, "五行").text = f"{gan5[gans.time]}{zhi_wuhangs[zhis.time]}"
    ET.SubElement(shizhu, "纳音").text = nayins.get((gans.time, zhis.time), "")
    
    # 十神分析
    shishen = ET.SubElement(bazi, "十神分析")
    me = gans.day
    
    # 计算十神
    gan_shens = [ten_deities[me][gan] for gan in gans]
    zhi_shens = []
    for zhi in zhis:
        shen_list = []
        for gan in zhi5[zhi]:
            shen_list.append(ten_deities[me][gan])
        zhi_shens.append(','.join(shen_list))
    
    # 天干十神
    tg_shishen = ET.SubElement(shishen, "天干十神")
    for i, gan in enumerate(gans):
        shen_info = ET.SubElement(tg_shishen, f"{'年月日时'[i]}柱")
        ET.SubElement(shen_info, "天干").text = gan
        ET.SubElement(shen_info, "十神").text = gan_shens[i]
    
    # 地支藏干十神
    dz_shishen = ET.SubElement(shishen, "地支藏干十神")
    for i, zhi in enumerate(zhis):
        shen_info = ET.SubElement(dz_shishen, f"{'年月日时'[i]}柱")
        ET.SubElement(shen_info, "地支").text = zhi
        ET.SubElement(shen_info, "藏干").text = ','.join(zhi5[zhi].keys())
        ET.SubElement(shen_info, "十神").text = zhi_shens[i]
    
    # 五行分析
    wuxing = ET.SubElement(bazi, "五行分析")
    
    # 计算五行分数
    scores = {"金":0, "木":0, "水":0, "火":0, "土":0}
    for item in gans:
        scores[gan5[item]] += 5
    
    for item in list(zhis) + [zhis.month]:
        for gan in zhi5[item]:
            scores[gan5[gan]] += zhi5[item][gan]
    
    # 五行得分
    scores_elem = ET.SubElement(wuxing, "五行得分")
    for wux, score in scores.items():
        score_elem = ET.SubElement(scores_elem, wux)
        score_elem.text = str(score)
    
    # 五行强弱
    strong_elem = ET.SubElement(wuxing, "五行强弱")
    total_score = sum(scores.values())
    for wux, score in scores.items():
        strength = "强" if score > total_score/5 else "弱"
        elem = ET.SubElement(strong_elem, wux)
        elem.text = strength
    
    # 日主强弱
    rizhu_qiangruo = ET.SubElement(wuxing, "日主强弱")
    
    # 计算日主强弱
    me_attrs = ten_deities[me].inverse
    strong_score = 0
    for item in gans:
        if item in [me_attrs['比'], me_attrs['劫']]:
            strong_score += 5
    
    for item in zhis:
        for gan in zhi5[item]:
            if gan in [me_attrs['比'], me_attrs['劫'], me_attrs['枭'], me_attrs['印']]:
                strong_score += zhi5[item][gan]
    
    rizhu_strength = "强" if strong_score > 29 else "弱"
    ET.SubElement(rizhu_qiangruo, "强度").text = rizhu_strength
    ET.SubElement(rizhu_qiangruo, "得分").text = str(strong_score)
    
    # 大运信息
    dayun = ET.SubElement(root, "大运信息")
    
    # 计算大运
    seq = Gan.index(gans.year)
    if is_female:
        direction = -1 if seq % 2 == 0 else 1
    else:
        direction = 1 if seq % 2 == 0 else -1
    
    gan_seq = Gan.index(gans.month)
    zhi_seq = Zhi.index(zhis.month)
    
    # 获取起运时间
    yun = ba.getYun(not is_female)
    start_age = yun.getStartAge()
    start_year = solar.getYear() + start_age
    
    dayuns = []
    for i in range(8):  # 计算8步大运
        gan_seq += direction
        zhi_seq += direction
        dayuns.append({
            '干支': Gan[gan_seq%10] + Zhi[zhi_seq%12],
            '年龄': start_age + i*10,
            '年份': start_year + i*10,
            '天干': Gan[gan_seq%10],
            '地支': Zhi[zhi_seq%12]
        })
    
    # 大运列表
    dayun_list = ET.SubElement(dayun, "大运列表")
    for i, dayun_info in enumerate(dayuns):
        dayun_elem = ET.SubElement(dayun_list, f"第{i+1}步大运")
        ET.SubElement(dayun_elem, "干支").text = dayun_info['干支']
        ET.SubElement(dayun_elem, "年龄").text = f"{dayun_info['年龄']}-{dayun_info['年龄']+9}岁"
        ET.SubElement(dayun_elem, "年份").text = f"{dayun_info['年份']}-{dayun_info['年份']+9}年"
        ET.SubElement(dayun_elem, "天干").text = dayun_info['天干']
        ET.SubElement(dayun_elem, "地支").text = dayun_info['地支']
        
        # 大运十神
        dayun_shishen = ten_deities[me][dayun_info['天干']]
        ET.SubElement(dayun_elem, "十神").text = dayun_shishen
        
        # 大运五行
        ET.SubElement(dayun_elem, "五行").text = f"{gan5[dayun_info['天干']]}{zhi_wuhangs[dayun_info['地支']]}"
    
    # 地支关系
    dizhi_guanxi = ET.SubElement(bazi, "地支关系")
    
    # 三合
    sanhe = ET.SubElement(dizhi_guanxi, "三合")
    for combo, result in gong_he.items():
        if all(zhi in zhis for zhi in combo):
            ET.SubElement(sanhe, "组合").text = f"{combo}合{result}"
    
    # 六合
    liuhe = ET.SubElement(dizhi_guanxi, "六合")
    for i, zhi1 in enumerate(zhis):
        for j, zhi2 in enumerate(zhis):
            if i < j and f"{zhi1}{zhi2}" in zhi_6he:
                ET.SubElement(liuhe, "组合").text = f"{zhi1}合{zhi2}"
    
    # 相冲
    xiangchong = ET.SubElement(dizhi_guanxi, "相冲")
    for i, zhi1 in enumerate(zhis):
        for j, zhi2 in enumerate(zhis):
            if i < j and f"{zhi1}{zhi2}" in zhi_chong:
                ET.SubElement(xiangchong, "组合").text = f"{zhi1}冲{zhi2}"
    
    # 格局分析
    geju = ET.SubElement(root, "格局分析")
    
    # 简单的格局判断
    patterns = []
    
    # 检查正官格
    if '官' in gan_shens or '官' in ''.join(zhi_shens):
        patterns.append("正官格")
    
    # 检查偏官格
    if '杀' in gan_shens or '杀' in ''.join(zhi_shens):
        patterns.append("偏官格")
    
    # 检查正财格
    if '财' in gan_shens or '财' in ''.join(zhi_shens):
        patterns.append("正财格")
    
    # 检查偏财格
    if '才' in gan_shens or '才' in ''.join(zhi_shens):
        patterns.append("偏财格")
    
    patterns_elem = ET.SubElement(geju, "格局")
    if patterns:
        for pattern in patterns:
            ET.SubElement(patterns_elem, "类型").text = pattern
    else:
        ET.SubElement(patterns_elem, "类型").text = "普通格局"
    
    # 美化XML输出
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    
    # 返回格式化的XML
    return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode('utf-8')

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="生成八字分析的XML格式数据")
    parser.add_argument("name", help="姓名")
    parser.add_argument("birthplace", help="出生地")
    parser.add_argument("year", type=int, help="出生年份")
    parser.add_argument("month", type=int, help="出生月份")
    parser.add_argument("day", type=int, help="出生日期")
    parser.add_argument("time", type=int, help="出生时辰 (0-23)")
    parser.add_argument("-f", "--female", action="store_true", help="女性")
    parser.add_argument("-l", "--lunar", action="store_true", help="农历日期")
    parser.add_argument("-o", "--output", help="输出文件路径")
    
    args = parser.parse_args()
    
    # 生成XML
    xml_output = create_bazi_xml(
        name=args.name,
        birthplace=args.birthplace,
        year=args.year,
        month=args.month,
        day=args.day,
        time=args.time,
        is_female=args.female,
        is_lunar=args.lunar
    )
    
    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(xml_output)
        print(f"XML已保存到: {args.output}")
    else:
        print(xml_output)

if __name__ == "__main__":
    main()
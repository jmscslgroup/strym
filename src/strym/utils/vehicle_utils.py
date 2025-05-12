#!/usr/bin/env python
# coding: utf-8

# Author : Rahul Bhadani
# License: MIT License

from urllib.request import urlopen, URLError
import json

vin_cache = {}

def decode_vin(vin):
    """Extract brand/manufacturer, model and yer

    Args:
        vin (str): The VIN to decode
        
    Returns:
        dict: A dictionary containing manufacturer, year, and model information
    """

    if len(vin) != 17:
        return {"error": "Invalid VIN Length. VINs must 17 characters."}
    
    result = {
        "manufacturer": manufacturer.get(vin[:3], "Unknown"),
        "year": year.get(vin[9], "Unknown"),
        "model": "Unknown",
        "wmi": "Unknown"
    }
    
    if vin in vin_cache:
        result["model"] = vin_cache[vin]
        return result
    
    # Check local VIN-to-model dictionary
    model_key = vin[:8]  # Use first 8 chars for model lookup
    if model_key in vin_to_model:
        result["model"] = vin_to_model[model_key]
        vin_cache[vin] = result["model"]  # Cache the result
        return result
    
    try:
        url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevin/{vin}?format=json"
        response = urlopen(url)
        data = json.loads(response.read().decode('utf-8'))
        
        # Extract model from API response
        api_model = next(
            (r["Value"] for r in data["Results"] if r["Variable"] == "Model"),
            "Unknown"
        )
        
        # Update result and cache
        result["model"] = api_model
        vin_cache[vin] = api_model
        return result
        
    except (URLError, KeyError, json.JSONDecodeError) as e:
        return {**result, "error": f"API failed: {str(e)}"}
    
# First three characters of VIN
manufacturer = {"AAA":"Audi","AAK":"FAW","AAM":"MAN","AAP":"VIN","AAV":"Volkswagen","AAW":"Challenger","A49":"TR-Tec","ABJ":"Mitsubishi","ABM":"BMW","ACV":"Isuzu","AC5":"Hyundai","AC9":"Beamish","ADB":"Mercedes-Benz","ADD":"UD_Trucks","ADM":"General_Motors","ADN":"Nissan","ADR":"Renault","ADX":"Tata","AE9":"Backdraft","AFA":"Ford","AFB":"Mazda","AFD":"BAIC","AFZ":"Fiat","AHH":"Hino","AHM":"Honda","AHT":"Toyota","BF9":"KIBO","BUK":"Kiira","BR1":"Mercedes-Benz","BRY":"FIAT","EAA":"Aurus","EAN":"Evolute","EAU":"Elektromobili","EBE":"Sollers","EBZ":"Nizhekotrans","ECE":"XCITE","ECW":"Trans-Alfa","DF9":"Laraki","HA0":"Wuxi","HA6":"Niu","HA7":"Jinan","HES":"smart","HGL":"Farizon","HGX":"Wuling","HHZ":"Huazi","HJR":"Jetour","HJ4":"BAW","HL4":"Zhejiang","HLX":"Li","HRV":"Beijing","HWM":"WM","HZ2":"Taizhou","HOD":"Taizhou","HOG":"Vichyton","JAA":"Isuzu","JAB":"Isuzu","JAC":"Isuzu","JAE":"Acura","JAL":"Isuzu","JAM":"Isuzu","JA3":"Mitsubishi","JA7":"Mitsubishi","JB3":"Dodge","JB4":"Dodge","JB7":"Dodge","JC0":"Ford","JC1":"Fiat","JC2":"Ford","JDA":"Daihatsu","JD1":"Daihatsu","JD2":"Daihatsu","JD4":"Daihatsu","JE3":"Eagle","JE4":"Mitsubishi","JF1":"Subaru","JF2":"Subaru","JF3":"Subaru","JF4":"Saab","JG1":"Chevrolet","JG2":"Pontiac","JG7":"Pontiac","JGC":"Chevrolet","JGT":"GMC","JHA":"Hino","JHB":"Hino","JHD":"Hino","JHF":"Hino","JHH":"Hino","JHL":"Honda","JHM":"Honda","JH1":"Honda","JH2":"Honda","JH3":"Honda","JN3":"Nissan","JN6":"Nissan","JN8":"Nissan","JPC":"Nissan","JP3":"Plymouth","JP4":"Plymouth","JP7":"Plymouth","JR2":"Isuzu","JSA":"Suzuki","JSK":"Kawasaki","JSL":"Kawasaki","JST":"Suzuki","JS1":"Suzuki","JS2":"Suzuki","JS3":"Suzuki","JS4":"Suzuki","JTB":"Toyota","JTD":"Toyota","JTE":"Toyota","JTF":"Toyota","JTG":"Toyota","JTH":"Lexus","JTJ":"Lexus","JTK":"Toyota","JTL":"Toyota","JTM":"Toyota","JTN":"Toyota","JTP":"Toyota","JT1":"Toyota","JT2":"Toyota","JT3":"Toyota","JT4":"Toyota","JT5":"Toyota","JT6":"Lexus","JT8":"Lexus","JW6":"Mitsubishi","JYA":"Yamaha","JYE":"Yamaha","JY3":"Yamaha","JY4":"Yamaha","J81":"Chevrolet","J87":"Pontiac","J8B":"Chevrolet","J8C":"Chevrolet","J8D":"GMC","J8T":"GMC","J8Z":"Chevrolet","KF3":"Merkavim","KF6":"Automotive","KF9":"Tomcar","KG9":"Charash","KL":"Daewoo","KLA":"Daewoo","KLP":"CT&T","KLT":"Tata","KLU":"Tata","KLY":"Daewoo","KL1":"GM","KL2":"Daewoo","KL3":"GM","KL4":"GM","KL5":"GM","KL6":"GM","KL7":"Daewoo","KL8":"GM","KM":"Hyundai","KMC":"Hyundai","KME":"Hyundai","KMF":"Hyundai","KMH":"Hyundai","KMJ":"Hyundai","KMT":"Genesis","KMU":"Genesis","KMX":"Hyundai","KMY":"Daelim","KM1":"Hyosung","KM4":"Hyosung","KM8":"Hyundai","KNA":"Kia","KNC":"Kia","KND":"Kia","KNE":"Kia","KNF":"Kia","KNG":"Kia","KNJ":"Ford","KNM":"Renault","KN1":"Asia","KN2":"Asia","KPA":"SsangYong","KPB":"SsangYong","KPH":"Mitsubishi","LAA":"Shanghai","LAE":"Jinan","LAL":"Sundiro","LAN":"Changzhou","LAP":"Chongqing","LAT":"Luoyang","LA6":"King","LA7":"Radar","LA8":"Anhui","LA9":"Beijing","LBB":"Zhejiang","LBE":"Beijing","LBM":"Zongshen","LBP":"Chongqing","LBV":"BMW","LBZ":"Yantai","LB1":"Fujian","LB2":"Geely","LB3":"Geely","LB4":"Chongqing","LB5":"Foshan","LB7":"Tibet","LCE":"Hangzhou","LCR":"Gonow","LCO":"BYD","LC2":"Changzhou","LC6":"Changzhou","LDD":"Dandong","LDF":"Dezhou","LDK":"FAW","LDN":"Soueast","LDP":"Dongfeng","LDY":"Zhongtong","LD3":"Guangdong","LD5":"Benzhou","LD9":"SiTech","LEC":"Tianjin","LEF":"Jiangling","LEH":"Zhejiang","LET":"Jiangling","LEW":"Dongfeng","LE4":"Beijing","LE8":"Guangzhou","LFB":"FAW","LFF":"Zhejiang","LFG":"Taizhou","LFJ":"Fujian","LFM":"FAW","LFN":"FAW","LFP":"FAW","LFT":"FAW","LFU":"Lifeng","LFV":"FAW","LFW":"FAW","LFX":"Sany","LFY":"Changshu","LFZ":"Leapmotor","LF3":"Lifan","LGA":"Dongfeng","LGW":"Great_Wall","LGX":"BYD","LGZ":"Guangzhou","LG6":"Dayun","LHA":"Shuanghuan","LHB":"Beijing","LHG":"GAC","LHJ":"Chongqing","LHM":"Dongfeng","LHW":"CRRC","LH0":"WM","LH1":"FAW","LJC":"Jincheng","LJD":"Yueda","LJM":"Sunlong","LJN":"Zhengzhou","LJR":"CIMC","LJS":"Yaxing","IUUL":"Shanghai","IUULI":"Lotus","LJV":"Sinotruk","LJVV":"JMC","LJX":"JMC","LJ1":"JAC","LJ4":"Shanghai","LJS":"Cixi","LJ8":"Zotye","LKC":"BAIC","LKG":"Youngman","LKH":"Hafei","LKL":"Higer","LKT":"Yunnan","LK2":"Anhui","LK6":"SAIC","LK8":"Zhejiang","LLC":"Loncin","LLJ":"Jiangsu","LLN":"Qoros","LLP":"Zhejiang","LLU":"Dongfeng","LLV":"Lifan","LLX":"Yudo","LL0":"Sanmen","LL2":"WM","LL3":"Xiamen","LL6":"GAC","LL8":"Jiangsu","LMC":"Suzuki","LME":"Skyworth","LMF":"Jiangmen","LMG":"GAC","LMH":"Jiangsu","LMP":"Geely","LMV":"Haima","LMW":"GAC","LMX":"Forthing","LM0":"Wangye","LM6":"SWM","LM8":"Seres","LNA":"GAC","LNB":"BAIC","LND":"JMEV","LNP":"NAC","LNN":"Chery","LNV":"Naveco","2ME":"Mercury","2MG":"Motor","2MH":"Mercury","2MR":"Mercury","2M9":"Motor","2NK":"Kenworth","2NP":"Peterbilt","2NV":"Nova","2P3":"Plymouth","2P4":"Plymouth","2P5":"Plymouth","2P9":"Prevost","2PC":"Prevost","2S2":"Suzuki","2S3":"Suzuki","2T1":"Toyota","2T2":"Lexus","2T3":"Toyota","2T9":"Triple","2V4":"Volkswagen","2V8":"Volkswagen","2W9":"Westward","2WK":"Western","2WL":"Western","2WM":"Western","2XK":"Kenworth","2XM":"Eagle","2XP":"Peterbilt","3A4":"Chrysler","3A8":"Chrysler","3A9":"MARGO","3AK":"Freightliner","3AL":"Freightliner","3AW":"Fruehauf"}
    
# 10th character of VIN
year = {"A":1980,"B":1981,"C":1982,"D":1983,"E":1984,"F":1985,"G":1986,"H":1987,"J":1988,"K":1989,"L":1990,"M":1991,"N":1992,"P":1993,"R":1994,"S":1995,"T":1996,"V":1997,"W":1998,"X":1999,"Y":2000,"1":2001,"2":2002,"3":2003,"4":2004,"5":2005,"6":2006,"7":2007,"8":2008,"9":2009,"A":2010,"B":2011,"C":2012,"D":2013,"E":2014,"F":2015,"G":2016,"H":2017,"J":2018,"K":2019,"L":2020,"M":2021,"N":2022,"P":2023,"R":2024,"S":2025,"T":2026,"V":2027,"W":2028,"X":2029}
    
#4th to 8th character of VIN
vin_to_model = {"2T3Y1RFV": "RAV4","1HGCM826": "AccordLX"}
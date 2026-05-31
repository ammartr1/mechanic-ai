#!/usr/bin/env python3
"""جامع بيانات المركبات من جميع المصادر"""

import wikipedia
import requests
from bs4 import BeautifulSoup
import json
import os
from pathlib import Path

DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

class VehicleDataCollector:
    def __init__(self):
        self.all_data = []
        
    def collect_wikipedia_vehicles(self):
        """جمع كل مقالات المركبات من ويكيبيديا"""
        print("[*] جمع بيانات ويكيبيديا...")
        
        vehicle_categories = [
            "List_of_car_brands", "List_of_automobile_manufacturers",
            "List_of_truck_manufacturers", "List_of_construction_equipment_manufacturers",
            "Internal_combustion_engine", "Electric_vehicle",
            "Engine_control_unit", "Anti-lock_braking_system",
            "List_of_auto_parts", "Transmission_(mechanical_device)",
            "Diesel_engine", "Turbocharger", "Common_rail",
            "On-board_diagnostics", "CAN_bus"
        ]
        
        wikipedia.set_lang("en")
        
        for category in vehicle_categories:
            try:
                page = wikipedia.page(category, auto_suggest=False)
                self.all_data.append({
                    "source": "wikipedia",
                    "title": page.title,
                    "content": page.summary,
                    "url": page.url
                })
                # جمع الروابط المرتبطة
                for link in page.links[:20]:
                    try:
                        sub_page = wikipedia.page(link, auto_suggest=False)
                        self.all_data.append({
                            "source": "wikipedia",
                            "title": sub_page.title,
                            "content": sub_page.summary,
                            "url": sub_page.url
                        })
                    except:
                        continue
            except Exception as e:
                print(f"[-] خطأ في جمع {category}: {e}")
                continue
        
        print(f"[✓] تم جمع {len(self.all_data)} مقالة")
    
    def collect_forum_repairs(self):
        """جمع بيانات التصليح من المنتديات العامة"""
        print("[*] جمع بيانات التصليح من المنتديات...")
        
        repair_urls = [
            "https://www.cargurus.com/Cars/Discussion-t1",
            "https://mechanics.stackexchange.com/questions",
            "https://www.reddit.com/r/MechanicAdvice/top.json?limit=100",
            "https://www.reddit.com/r/Justrolledintotheshop/top.json?limit=100"
        ]
        
        for url in repair_urls:
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, headers=headers, timeout=10)
                
                if "reddit.com" in url:
                    data = response.json()
                    for post in data.get("data", {}).get("children", []):
                        post_data = post["data"]
                        self.all_data.append({
                            "source": "reddit",
                            "title": post_data.get("title", ""),
                            "content": post_data.get("selftext", ""),
                            "url": f"https://reddit.com{post_data.get('permalink', '')}"
                        })
                else:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # استخراج الأسئلة والإجابات
                    for div in soup.find_all(['div', 'article']):
                        text = div.get_text(strip=True)
                        if len(text) > 100:
                            self.all_data.append({
                                "source": "forum",
                                "content": text,
                                "url": url
                            })
            except Exception as e:
                print(f"[-] خطأ في جمع {url}: {e}")
                continue
        
        print(f"[✓] تم جمع {len(self.all_data)} إجمالاً")
    
    def save_dataset(self):
        """حفظ كل البيانات"""
        with open(DATA_DIR / "vehicle_knowledge.json", "w", encoding="utf-8") as f:
            json.dump(self.all_data, f, ensure_ascii=False, indent=2)
        print(f"[✓] تم حفظ {len(self.all_data)} سجل في vehicle_knowledge.json")

if __name__ == "__main__":
    collector = VehicleDataCollector()
    collector.collect_wikipedia_vehicles()
    collector.collect_forum_repairs()
    collector.save_dataset()
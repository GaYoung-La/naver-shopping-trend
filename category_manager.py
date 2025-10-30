"""
카테고리 및 키워드 관리 모듈
- 계층적 카테고리 구조 (대분류 > 중분류 > 소분류)
- 자동 키워드 + 사용자 지정 키워드 관리
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime


class CategoryManager:
    """카테고리 및 키워드 관리 클래스"""
    
    def __init__(self, data_path: str = "./categories_hierarchical.json"):
        self.data_path = Path(data_path)
        self.data = self._load_or_init()
    
    def _load_or_init(self) -> Dict:
        """데이터 로드 또는 초기화"""
        if self.data_path.exists():
            with open(self.data_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return self._init_structure()
    
    def _init_structure(self) -> Dict:
        """초기 계층 구조 생성"""
        return {
            "패션의류": {
                "auto_keywords": [],
                "user_keywords": [],
                "enabled_keywords": [],  # 활성화된 키워드 목록
                "subcategories": {
                    "여성의류": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "남성의류": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "언더웨어": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                }
            },
            "패션잡화": {
                "auto_keywords": [],
                "user_keywords": [],
                "enabled_keywords": [],
                "subcategories": {
                    "여성가방": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "남성가방": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "지갑": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                }
            },
            "화장품/미용": {
                "auto_keywords": [],
                "user_keywords": [],
                "enabled_keywords": [],
                "subcategories": {
                    "스킨케어": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "메이크업": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "향수": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                }
            },
            "디지털/가전": {
                "auto_keywords": [],
                "user_keywords": [],
                "enabled_keywords": [],
                "subcategories": {}
            },
            "식품": {
                "auto_keywords": [],
                "user_keywords": [],
                "enabled_keywords": [],
                "subcategories": {
                    "농수축산물": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "가공식품": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "건강식품": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                }
            },
            "생활/건강": {
                "auto_keywords": [],
                "user_keywords": [],
                "enabled_keywords": [],
                "subcategories": {
                    "생활용품": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "건강용품": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "의료용품": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                }
            },
            "출산/육아": {
                "auto_keywords": [],
                "user_keywords": [],
                "enabled_keywords": [],
                "subcategories": {
                    "기저귀": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "분유": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                    "이유식": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                }
            },
            "스포츠/레저": {
                "auto_keywords": [],
                "user_keywords": [],
                "enabled_keywords": [],
                "subcategories": {}
            },
            "여가/생활편의": {
                "auto_keywords": [],
                "user_keywords": [],
                "enabled_keywords": [],
                "subcategories": {}
            }
        }
    
    def migrate_from_old_format(self, old_data_path: str = "./naver_categories.json"):
        """기존 평면 구조에서 계층 구조로 마이그레이션"""
        old_path = Path(old_data_path)
        
        if not old_path.exists():
            print("⚠️ 기존 데이터가 없습니다.")
            return
        
        with open(old_path, "r", encoding="utf-8") as f:
            old_data = json.load(f)
        
        print(f"📦 기존 데이터 마이그레이션 시작: {len(old_data)}개 카테고리")
        
        for category, keywords in old_data.items():
            # 대분류만 있는 경우
            if category in self.data:
                self.data[category]["auto_keywords"] = keywords
                self.data[category]["enabled_keywords"] = keywords.copy()  # 기본적으로 모두 활성화
                print(f"✓ {category}: {len(keywords)}개 키워드")
        
        self.save()
        print(f"✅ 마이그레이션 완료!")
    
    def get_major_categories(self) -> List[str]:
        """대분류 목록 반환"""
        return list(self.data.keys())
    
    def get_subcategories(self, major: str) -> List[str]:
        """중분류 목록 반환"""
        if major not in self.data:
            return []
        return list(self.data[major].get("subcategories", {}).keys())
    
    def add_user_keyword(self, major: str, keyword: str, sub: Optional[str] = None):
        """사용자 지정 키워드 추가"""
        if major not in self.data:
            print(f"❌ 카테고리 '{major}'가 존재하지 않습니다.")
            return False
        
        target = self.data[major]
        if sub:
            if sub not in target.get("subcategories", {}):
                print(f"❌ 중분류 '{sub}'가 존재하지 않습니다.")
                return False
            target = target["subcategories"][sub]
        
        # 중복 체크
        if keyword in target["user_keywords"]:
            print(f"⚠️ '{keyword}'는 이미 존재합니다.")
            return False
        
        target["user_keywords"].append(keyword)
        target["enabled_keywords"].append(keyword)
        self.save()
        print(f"✅ '{keyword}' 추가 완료!")
        return True
    
    def remove_user_keyword(self, major: str, keyword: str, sub: Optional[str] = None):
        """사용자 지정 키워드 제거"""
        if major not in self.data:
            return False
        
        target = self.data[major]
        if sub:
            if sub not in target.get("subcategories", {}):
                return False
            target = target["subcategories"][sub]
        
        if keyword in target["user_keywords"]:
            target["user_keywords"].remove(keyword)
            if keyword in target["enabled_keywords"]:
                target["enabled_keywords"].remove(keyword)
            self.save()
            return True
        
        return False
    
    def enable_keyword(self, major: str, keyword: str, sub: Optional[str] = None):
        """키워드 활성화"""
        if major not in self.data:
            return False
        
        target = self.data[major]
        if sub:
            if sub not in target.get("subcategories", {}):
                return False
            target = target["subcategories"][sub]
        
        # 자동 또는 사용자 키워드에 존재해야 함
        all_keywords = target["auto_keywords"] + target["user_keywords"]
        
        if keyword in all_keywords and keyword not in target["enabled_keywords"]:
            target["enabled_keywords"].append(keyword)
            self.save()
            return True
        
        return False
    
    def disable_keyword(self, major: str, keyword: str, sub: Optional[str] = None):
        """키워드 비활성화"""
        if major not in self.data:
            return False
        
        target = self.data[major]
        if sub:
            if sub not in target.get("subcategories", {}):
                return False
            target = target["subcategories"][sub]
        
        if keyword in target["enabled_keywords"]:
            target["enabled_keywords"].remove(keyword)
            self.save()
            return True
        
        return False
    
    def get_all_keywords(self, major: str, sub: Optional[str] = None, only_enabled: bool = False) -> Dict[str, List[str]]:
        """
        모든 키워드 반환
        
        중분류를 선택했는데 키워드가 없으면 대분류 키워드를 반환
        
        Returns:
            {
                "auto": [...],      # 자동 수집 키워드
                "user": [...],      # 사용자 지정 키워드
                "enabled": [...]    # 활성화된 키워드
            }
        """
        if major not in self.data:
            return {"auto": [], "user": [], "enabled": []}
        
        target = self.data[major]
        if sub:
            if sub not in target.get("subcategories", {}):
                return {"auto": [], "user": [], "enabled": []}
            target = target["subcategories"][sub]
        
        # 결과 구성
        result = {
            "auto": target.get("auto_keywords", []),
            "user": target.get("user_keywords", []),
            "enabled": target.get("enabled_keywords", [])
        }
        
        # 중분류인데 키워드가 하나도 없으면 대분류 키워드 사용
        if sub and not result["auto"] and not result["user"] and not result["enabled"]:
            major_target = self.data[major]
            result = {
                "auto": major_target.get("auto_keywords", []),
                "user": major_target.get("user_keywords", []),
                "enabled": major_target.get("enabled_keywords", [])
            }
        
        if only_enabled:
            return {
                "auto": [],
                "user": [],
                "enabled": result["enabled"]
            }
        
        return result
    
    def get_enabled_keywords(self, major: str, sub: Optional[str] = None) -> List[str]:
        """
        활성화된 키워드만 반환 (분석에 사용)
        
        중분류를 선택했는데 키워드가 없으면 대분류 키워드를 사용
        """
        keywords = self.get_all_keywords(major, sub, only_enabled=True)
        enabled = keywords["enabled"]
        
        # 중분류를 선택했는데 키워드가 없으면 대분류 키워드 사용
        if sub and not enabled:
            print(f"💡 '{sub}' 중분류에 키워드가 없어 '{major}' 대분류 키워드 사용")
            major_keywords = self.get_all_keywords(major, sub=None, only_enabled=True)
            enabled = major_keywords["enabled"]
        
        return enabled
    
    def update_auto_keywords(self, major: str, keywords: List[str], sub: Optional[str] = None, mode: str = "replace"):
        """
        자동 수집 키워드 업데이트
        
        Args:
            mode: "replace" (교체) 또는 "merge" (병합)
        """
        if major not in self.data:
            return False
        
        target = self.data[major]
        if sub:
            if sub not in target.get("subcategories", {}):
                return False
            target = target["subcategories"][sub]
        
        if mode == "replace":
            # 기존 자동 키워드를 새로운 것으로 교체
            target["auto_keywords"] = keywords
            # enabled_keywords도 업데이트 (사용자 키워드는 유지)
            target["enabled_keywords"] = keywords + target.get("user_keywords", [])
        else:  # merge
            # 기존 + 신규 병합 (중복 제거)
            existing = set(target.get("auto_keywords", []))
            new_keywords = list(existing | set(keywords))
            target["auto_keywords"] = new_keywords
            
            # enabled도 업데이트
            enabled_set = set(target.get("enabled_keywords", []))
            target["enabled_keywords"] = list(enabled_set | set(keywords))
        
        self.save()
        return True
    
    def add_subcategory(self, major: str, sub_name: str):
        """중분류 추가"""
        if major not in self.data:
            return False
        
        if sub_name in self.data[major].get("subcategories", {}):
            print(f"⚠️ '{sub_name}'는 이미 존재합니다.")
            return False
        
        if "subcategories" not in self.data[major]:
            self.data[major]["subcategories"] = {}
        
        self.data[major]["subcategories"][sub_name] = {
            "auto_keywords": [],
            "user_keywords": [],
            "enabled_keywords": []
        }
        
        self.save()
        return True
    
    def save(self):
        """데이터 저장"""
        # 백업
        if self.data_path.exists():
            backup_path = self.data_path.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            import shutil
            shutil.copy(self.data_path, backup_path)
        
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def get_stats(self) -> Dict:
        """전체 통계"""
        total_major = len(self.data)
        total_sub = sum(len(v.get("subcategories", {})) for v in self.data.values())
        total_auto = sum(len(v.get("auto_keywords", [])) for v in self.data.values())
        total_user = sum(len(v.get("user_keywords", [])) for v in self.data.values())
        total_enabled = sum(len(v.get("enabled_keywords", [])) for v in self.data.values())
        
        return {
            "대분류": total_major,
            "중분류": total_sub,
            "자동 키워드": total_auto,
            "사용자 키워드": total_user,
            "활성화 키워드": total_enabled
        }


def migrate_old_data():
    """기존 데이터 마이그레이션 스크립트"""
    manager = CategoryManager()
    manager.migrate_from_old_format()
    
    print("\n📊 마이그레이션 완료 통계:")
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}개")


if __name__ == "__main__":
    # 마이그레이션 실행
    migrate_old_data()


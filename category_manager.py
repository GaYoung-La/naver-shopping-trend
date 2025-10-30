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
        """데이터 로드 또는 초기화 (SEED_QUERIES와 병합)"""
        if self.data_path.exists():
            with open(self.data_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            
            # SEED_QUERIES 구조와 병합 (새 카테고리 추가)
            updated_data = self._merge_with_seed_queries(existing_data)
            
            # 새 카테고리가 추가되었으면 저장
            if updated_data != existing_data:
                print(f"🔄 새로운 카테고리 추가됨, 저장 중...")
                with open(self.data_path, "w", encoding="utf-8") as f:
                    json.dump(updated_data, f, ensure_ascii=False, indent=2)
            
            return updated_data
        else:
            return self._init_structure()
    
    def _merge_with_seed_queries(self, existing_data: Dict) -> Dict:
        """기존 데이터와 SEED_QUERIES 병합"""
        try:
            from auto_keyword_discovery import SEED_QUERIES
            
            # SEED_QUERIES의 모든 카테고리 확인
            for major_cat, cat_data in SEED_QUERIES.items():
                # 대분류가 없으면 추가
                if major_cat not in existing_data:
                    print(f"  ➕ 대분류 추가: {major_cat}")
                    existing_data[major_cat] = {
                        "auto_keywords": [],
                        "user_keywords": [],
                        "enabled_keywords": [],
                        "subcategories": {}
                    }
                
                # 중분류 확인
                if "중분류" in cat_data and cat_data["중분류"]:
                    if "subcategories" not in existing_data[major_cat]:
                        existing_data[major_cat]["subcategories"] = {}
                    
                    for sub_cat in cat_data["중분류"].keys():
                        # 중분류가 없으면 추가
                        if sub_cat not in existing_data[major_cat]["subcategories"]:
                            print(f"     ➕ 중분류 추가: {major_cat} > {sub_cat}")
                            existing_data[major_cat]["subcategories"][sub_cat] = {
                                "auto_keywords": [],
                                "user_keywords": [],
                                "enabled_keywords": []
                            }
            
            return existing_data
            
        except Exception as e:
            print(f"⚠️ SEED_QUERIES 병합 실패: {e}")
            return existing_data
    
    def _init_structure(self) -> Dict:
        """초기 계층 구조 생성 (SEED_QUERIES 기반)"""
        try:
            # SEED_QUERIES를 import하여 구조 생성
            from auto_keyword_discovery import SEED_QUERIES
            
            structure = {}
            for major_cat, cat_data in SEED_QUERIES.items():
                structure[major_cat] = {
                    "auto_keywords": [],
                    "user_keywords": [],
                    "enabled_keywords": [],
                    "subcategories": {}
                }
                
                # 중분류가 있으면 추가
                if "중분류" in cat_data and cat_data["중분류"]:
                    for sub_cat in cat_data["중분류"].keys():
                        structure[major_cat]["subcategories"][sub_cat] = {
                            "auto_keywords": [],
                            "user_keywords": [],
                            "enabled_keywords": []
                        }
            
            print(f"✅ SEED_QUERIES 기반 구조 생성: {len(structure)}개 대분류")
            return structure
            
        except Exception as e:
            # SEED_QUERIES를 import할 수 없으면 기본 구조 반환
            print(f"⚠️ SEED_QUERIES import 실패, 기본 구조 사용: {e}")
            return {
                "패션의류": {
                    "auto_keywords": [],
                    "user_keywords": [],
                    "enabled_keywords": [],
                    "subcategories": {
                        "여성의류": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                        "남성의류": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
                        "언더웨어": {"auto_keywords": [], "user_keywords": [], "enabled_keywords": []},
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
                }
            }
    
    def migrate_from_old_format(self, old_data_path: str = "./naver_categories.json"):
        """
        기존 평면 구조에서 계층 구조로 마이그레이션
        
        주의: 키워드는 마이그레이션하지 않음 (업데이트로만 추가)
        """
        old_path = Path(old_data_path)
        
        if not old_path.exists():
            print("⚠️ 기존 데이터가 없습니다.")
            return
        
        print("ℹ️  기존 키워드는 마이그레이션하지 않습니다.")
        print("   '🔄 키워드 자동 업데이트'를 실행하세요.")
        
        self.save()
        print(f"✅ 카테고리 구조 생성 완료!")
    
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
    
    def enable_all_keywords(self, major: str, sub: Optional[str] = None):
        """모든 키워드 활성화"""
        if major not in self.data:
            return False
        
        target = self.data[major]
        if sub:
            if sub not in target.get("subcategories", {}):
                return False
            target = target["subcategories"][sub]
        
        # 자동 + 사용자 키워드 모두 활성화
        all_keywords = list(set(target.get("auto_keywords", []) + target.get("user_keywords", [])))
        target["enabled_keywords"] = all_keywords
        self.save()
        return True
    
    def disable_all_keywords(self, major: str, sub: Optional[str] = None):
        """모든 키워드 비활성화"""
        if major not in self.data:
            return False
        
        target = self.data[major]
        if sub:
            if sub not in target.get("subcategories", {}):
                return False
            target = target["subcategories"][sub]
        
        # 모든 키워드 비활성화
        target["enabled_keywords"] = []
        self.save()
        return True
    
    def get_all_keywords(self, major: str, sub: Optional[str] = None, only_enabled: bool = False) -> Dict[str, List[str]]:
        """
        모든 키워드 반환
        
        - 중분류 선택 시: 해당 중분류의 키워드만
        - 대분류 전체 선택 시: 대분류 + 모든 중분류 키워드 병합
        
        Returns:
            {
                "auto": [...],      # 자동 수집 키워드
                "user": [...],      # 사용자 지정 키워드
                "enabled": [...]    # 활성화된 키워드
            }
        """
        if major not in self.data:
            return {"auto": [], "user": [], "enabled": []}
        
        # 중분류 선택한 경우: 해당 중분류만
        if sub:
            target = self.data[major]
            if sub not in target.get("subcategories", {}):
                return {"auto": [], "user": [], "enabled": []}
            target = target["subcategories"][sub]
            
            result = {
                "auto": target.get("auto_keywords", []),
                "user": target.get("user_keywords", []),
                "enabled": target.get("enabled_keywords", [])
            }
            
            if only_enabled:
                return {
                    "auto": [],
                    "user": [],
                    "enabled": result["enabled"]
                }
            
            return result
        
        # 대분류 전체 선택: 대분류 + 모든 중분류 병합
        major_data = self.data[major]
        
        all_auto = set(major_data.get("auto_keywords", []))
        all_user = set(major_data.get("user_keywords", []))
        all_enabled = set(major_data.get("enabled_keywords", []))
        
        # 모든 중분류 키워드 병합
        subcategories = major_data.get("subcategories", {})
        for sub_name, sub_data in subcategories.items():
            all_auto.update(sub_data.get("auto_keywords", []))
            all_user.update(sub_data.get("user_keywords", []))
            all_enabled.update(sub_data.get("enabled_keywords", []))
        
        result = {
            "auto": sorted(list(all_auto)),
            "user": sorted(list(all_user)),
            "enabled": sorted(list(all_enabled))
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
        
        - 중분류 선택 시: 해당 중분류의 키워드만 반환
        - 대분류 전체 선택 시: 대분류 + 모든 중분류 키워드 병합
        """
        if major not in self.data:
            return []
        
        # 중분류 선택한 경우: 해당 중분류만
        if sub:
            keywords = self.get_all_keywords(major, sub, only_enabled=True)
            return keywords["enabled"]
        
        # 대분류 전체 선택: 대분류 + 모든 중분류 병합
        all_enabled = set()
        
        # 대분류 키워드
        major_keywords = self.data[major].get("enabled_keywords", [])
        all_enabled.update(major_keywords)
        
        # 모든 중분류 키워드 병합
        subcategories = self.data[major].get("subcategories", {})
        for sub_name, sub_data in subcategories.items():
            sub_enabled = sub_data.get("enabled_keywords", [])
            all_enabled.update(sub_enabled)
        
        return sorted(list(all_enabled))
    
    def update_auto_keywords(self, major: str, keywords: List[str], sub: Optional[str] = None):
        """
        자동 수집 키워드 업데이트 (항상 교체 모드)
        
        Args:
            major: 대분류 이름
            keywords: 새로운 키워드 리스트
            sub: 중분류 이름 (선택사항)
        """
        if major not in self.data:
            return False
        
        target = self.data[major]
        if sub:
            if sub not in target.get("subcategories", {}):
                return False
            target = target["subcategories"][sub]
        
        # 기존 자동 키워드를 새로운 것으로 교체
        target["auto_keywords"] = keywords
        
        # enabled_keywords도 업데이트 (사용자 키워드는 유지)
        user_keywords = target.get("user_keywords", [])
        target["enabled_keywords"] = keywords + user_keywords
        
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


"""
Skill Detector — Escanea y detecta skills de múltiples proveedores
Proveedores soportados: Claude Code, OpenCode, Kilocode, Antigravity, Hermes
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class SkillInfo:
    """Información de una skill detectada"""
    name: str
    provider: str
    path: str
    description: str = ""
    enabled: bool = False
    installed_at: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self):
        return asdict(self)


class SkillDetector:
    """Detector de skills multi-proveedor"""
    
    PROVIDER_PATHS = {
        "claude-code": Path.home() / ".claude" / "skills",
        "opencode": Path.home() / ".opencode" / "skills",
        "kilocode": Path.home() / ".kilocode" / "skills",
        "antigravity": Path.home() / ".antigravity" / "providers",
        "hermes": Path.home() / ".hermes" / "skills",
        "agency": Path.home() / ".hermes" / "hermes-agent" / "skills" / "agency",
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (Path.home() / ".hermes" / "memory" / "skills_config.json")
        self.enabled_skills = self._load_enabled()
    
    def _load_enabled(self) -> Dict[str, bool]:
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text())
                return {k: v for k, v in data.items()}
            except Exception:
                pass
        return {}
    
    def _save_enabled(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(self.enabled_skills, indent=2))
    
    def detect_all(self) -> List[SkillInfo]:
        skills = []
        for provider, skills_dir in self.PROVIDER_PATHS.items():
            if not skills_dir.exists():
                continue
            if provider == "claude-code":
                skills.extend(self._detect_claude_skills(skills_dir))
            elif provider == "opencode":
                skills.extend(self._detect_opencode_skills(skills_dir))
            elif provider == "kilocode":
                skills.extend(self._detect_kilocode_skills(skills_dir))
            elif provider == "antigravity":
                skills.extend(self._detect_antigravity_skills(skills_dir))
            elif provider == "hermes":
                skills.extend(self._detect_hermes_skills(skills_dir))
            elif provider == "agency":
                skills.extend(self._detect_agency_skills(skills_dir))
        return skills
    
    def _detect_claude_skills(self, skills_dir: Path) -> List[SkillInfo]:
        skills = []
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                name = skill_dir.name
                description = self._parse_description(skill_file)
                key = f"claude-code.{name}"
                skills.append(SkillInfo(
                    name=name, provider="claude-code", path=str(skill_dir),
                    description=description, enabled=self.enabled_skills.get(key, False),
                    installed_at=str(skill_file.stat().st_mtime), tags=["claude", "ai-assistant"]
                ))
        return skills
    
    def _detect_opencode_skills(self, skills_dir: Path) -> List[SkillInfo]:
        skills = []
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                name = skill_dir.name
                description = self._parse_description(skill_file)
                key = f"opencode.{name}"
                skills.append(SkillInfo(
                    name=name, provider="opencode", path=str(skill_dir),
                    description=description, enabled=self.enabled_skills.get(key, False),
                    installed_at=str(skill_file.stat().st_mtime), tags=["opencode", "coding"]
                ))
        return skills
    
    def _detect_kilocode_skills(self, skills_dir: Path) -> List[SkillInfo]:
        skills = []
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                name = skill_dir.name
                description = self._parse_description(skill_file)
                key = f"kilocode.{name}"
                skills.append(SkillInfo(
                    name=name, provider="kilocode", path=str(skill_dir),
                    description=description, enabled=self.enabled_skills.get(key, False),
                    installed_at=str(skill_file.stat().st_mtime), tags=["kilocode"]
                ))
        return skills
    
    def _detect_antigravity_skills(self, providers_dir: Path) -> List[SkillInfo]:
        skills = []
        if not providers_dir.exists():
            return skills
        for provider_dir in providers_dir.iterdir():
            if not provider_dir.is_dir():
                continue
            for skill_dir in provider_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    name = f"{provider_dir.name}.{skill_dir.name}"
                    description = self._parse_description(skill_file)
                    key = f"antigravity.{provider_dir.name}.{skill_dir.name}"
                    skills.append(SkillInfo(
                        name=name, provider="antigravity", path=str(skill_dir),
                        description=description, enabled=self.enabled_skills.get(key, False),
                        installed_at=str(skill_file.stat().st_mtime),
                        tags=["antigravity", provider_dir.name]
                    ))
        return skills
    
    def _detect_agency_skills(self, skills_dir: Path) -> List[SkillInfo]:
        skills = []
        if not skills_dir.exists():
            return skills
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                name = skill_dir.name
                description = self._parse_description(skill_file)
                key = f"agency.{name}"
                skills.append(SkillInfo(
                    name=name, provider="agency", path=str(skill_dir),
                    description=description, enabled=self.enabled_skills.get(key, False),
                    installed_at=str(skill_file.stat().st_mtime), tags=["agency", "external"]
                ))
        return skills

    def _detect_hermes_skills(self, skills_dir: Path) -> List[SkillInfo]:
        skills = []
        if not skills_dir.exists():
            return skills
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                name = skill_dir.name
                description = self._parse_description(skill_file)
                key = f"hermes.{name}"
                skills.append(SkillInfo(
                    name=name, provider="hermes", path=str(skill_dir),
                    description=description, enabled=self.enabled_skills.get(key, False),
                    installed_at=str(skill_file.stat().st_mtime), tags=["hermes", "core"]
                ))
        return skills
    
    def _parse_description(self, skill_file: Path) -> str:
        try:
            content = skill_file.read_text()
            lines = [l.strip() for l in content.split(chr(10)) if l.strip()]
            for line in lines:
                if not line.startswith('#') and len(line) > 10:
                    return line[:200]
        except Exception:
            pass
        return "Skill descargada"
    
    def get_providers(self) -> List[Dict]:
        skills = self.detect_all()
        providers = {}
        for skill in skills:
            if skill.provider not in providers:
                providers[skill.provider] = {
                    "name": skill.provider, "total": 0, "enabled": 0, "skills": []
                }
            providers[skill.provider]["total"] += 1
            if skill.enabled:
                providers[skill.provider]["enabled"] += 1
            providers[skill.provider]["skills"].append(skill.to_dict())
        return list(providers.values())
    
    def toggle_skill(self, provider: str, skill_name: str, enabled: bool) -> bool:
        key = f"{provider}.{skill_name}"
        self.enabled_skills[key] = enabled
        self._save_enabled()
        return True
    
    def get_skill(self, provider: str, skill_name: str) -> Optional[SkillInfo]:
        for s in self.detect_all():
            if s.provider == provider and s.name == skill_name:
                return s
        return None

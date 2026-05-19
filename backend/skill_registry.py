
"""
SkillRegistry: Versión simple — carga desde JSON al iniciar.
"""

from pathlib import Path
import json, hashlib
from dataclasses import dataclass, asdict
from typing import Dict, List
import shutil

@dataclass
class GlobalSkill:
    id: str
    name: str
    description: str
    canonical_path: str
    code_hash: str
    tags: List
    providers: List
    created_at: str
    is_fork: bool = False

class SimpleSkillRegistry:
    GLOBAL_SKILLS_DIR = Path.home() / ".hermes" / "global_skills"
    REGISTRY_DB = Path.home() / ".hermes" / "memory" / "skill_registry.json"
    
    PROVIDER_SOURCES = {
        "claude-code": Path.home() / ".claude" / "skills",
        "opencode": Path.home() / ".opencode" / "skills",
        "kilocode": Path.home() / ".kilocode" / "skills",
        "antigravity": Path.home() / ".antigravity" / "providers",
        "hermes": Path.home() / ".hermes" / "skills",
        # "agency": Path.home() / ".hermes" / "hermes-agent" / "skills" / "agency",
    }
    
    def __init__(self):
        self.global_skills: Dict[str, GlobalSkill] = {}
        self.provider_index: Dict[str, str] = {}
        self.load()
    
    def _quick_hash(self, skill_dir: Path) -> str:
        h = hashlib.sha256()
        md = skill_dir / "SKILL.md"
        if md.exists():
            st = md.stat()
            h.update(f"md:{st.st_size}:{int(st.st_mtime)}".encode())
        for f in skill_dir.iterdir():
            if f.is_file() and f.suffix in ['.cp', '.py']:
                st = f.stat()
                h.update(f"{f.name}:{st.st_size}:{int(st.st_mtime)}".encode())
                break
        return h.hexdigest()[:16]
    
    def _quick_desc(self, md_path: Path) -> str:
        try:
            line = md_path.read_text().split('\n')[0].strip()
            return line[:200] if line else "Skill"
        except: return "Skill"
    
    def load(self):
        if self.REGISTRY_DB.exists():
            try:
                data = json.loads(self.REGISTRY_DB.read_text())
                self.global_skills = {k: GlobalSkill(**v) for k, v in data["global_skills"].items()}
                self.provider_index = data["provider_index"]
                print(f"[Registry] Cargado: {len(self.global_skills)} skills")
                return self
            except Exception as e:
                print(f"[Registry] Error: {e}")
        print("[Registry] Escaneando...")
        self._fast_scan()
        self.save()
        return self
    
    def rescan(self):
        self._fast_scan()
        self.save()
        return self
    
    def _fast_scan(self):
        self.global_skills.clear()
        self.provider_index.clear()
        self.GLOBAL_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        
        for skill_dir in self.GLOBAL_SKILLS_DIR.iterdir():
            if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
                continue
            name = skill_dir.name
            sid = self._quick_hash(skill_dir)
            self.global_skills[sid] = GlobalSkill(
                id=sid, name=name, description=self._quick_desc(skill_dir / "SKILL.md"),
                canonical_path=str(skill_dir), code_hash=sid,
                tags=[], providers=[], created_at="2024-01-01", is_fork=False
            )
        
        for provider, src in self.PROVIDER_SOURCES.items():
            if not src.exists(): continue
            # Collect all skill directories (direct + nested in categories)
            skill_dirs = []
            for item in src.iterdir():
                if not item.is_dir():
                    continue
                if (item / "SKILL.md").exists():
                    # Direct skill: ~/.hermes/skills/skillname/
                    skill_dirs.append((item.name, item, None))
                else:
                    # Check subdirs for categorized skills: ~/.hermes/skills/category/skillname/
                    for sub in item.iterdir():
                        if sub.is_dir() and (sub / "SKILL.md").exists():
                            skill_dirs.append((sub.name, sub, item.name))  # (skill_name, path, category)
            
            for name, skill_dir, category_hint in skill_dirs:
                lhash = self._quick_hash(skill_dir)
                matched = None
                if skill_dir.is_symlink():
                    try:
                        target = str(skill_dir.resolve())
                        for gid, gs in self.global_skills.items():
                            if gs.name == name and gs.canonical_path == target:
                                matched = gid; break
                    except: pass
                if matched is None:
                    for gid, gs in self.global_skills.items():
                        if gs.name == name and gs.code_hash == lhash:
                            matched = gid; break
                key = f"{provider}.{name}"
                if matched:
                    self.provider_index[key] = matched
                    self.global_skills[matched].providers.append({
                        "name": provider, "enabled": True, "overrides": {},
                        "local_path": str(skill_dir)
                    })
                else:
                    # Skill existe solo en este provider → crear entrada global
                    sid = self._quick_hash(skill_dir)
                    self.global_skills[sid] = GlobalSkill(
                        id=sid, name=name, description=self._quick_desc(skill_dir / "SKILL.md"),
                        canonical_path=str(skill_dir), code_hash=sid,
                        tags=[], providers=[{
                            "name": provider, "enabled": True, "overrides": {},
                            "local_path": str(skill_dir)
                        }], created_at="2024-01-01", is_fork=False
                    )
                    self.provider_index[key] = sid
        print(f"[Registry] Scan: {len(self.global_skills)} skills")
    
    def save(self):
        self.REGISTRY_DB.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "global_skills": {k: asdict(v) for k, v in self.global_skills.items()},
            "provider_index": self.provider_index,
            "updated_at": "2024-01-01"
        }
        self.REGISTRY_DB.write_text(json.dumps(data, indent=2))
    
    def _get_category(self, skill):
        """Extrae categoría del path de la skill.
        
        Reglas:
        - skills/category/skillname/ → category
        - skills/skillname/ → 'general' (skill directa, sin categoría)
        - agency/skills/agency/skillname/ → 'agency' (path especial de agency)
        """
        for path in [skill.canonical_path] + [p.get('local_path', '') for p in skill.providers]:
            if '/skills/' in path:
                after_skills = path.split('/skills/')[1].strip('/')
                if not after_skills:
                    continue
                parts = after_skills.split('/')
                # Si hay 2+ niveles → skills/category/skill/ → category es el primero
                if len(parts) >= 2:
                    # Excepción: si el primer nivel es el mismo nombre que la skill,
                    # significa que es un path tipo ~/.claude/skills/skillname/
                    # donde skillname es la carpeta de la skill, no una categoría
                    if parts[0] == skill.name:
                        return 'general'
                    return parts[0]
                # Si hay 1 nivel → skills/skillname/ → general
                elif len(parts) == 1:
                    return 'general'
        return 'uncategorized'
    
    def get_providers(self):
        providers = {}
        for skill in self.global_skills.values():
            # Skip agency skills entirely
            if skill.name.startswith("agency-"):
                continue
            category = self._get_category(skill)
            for p in skill.providers:
                pn = p['name']
                if pn not in providers:
                    providers[pn] = {"name": pn, "total": 0, "enabled": 0, "skills": []}
                providers[pn]["total"] += 1
                if p.get("enabled"): providers[pn]["enabled"] += 1
                providers[pn]["skills"].append({
                    "name": skill.name, "description": skill.description,
                    "enabled": p.get("enabled", False), "tags": skill.tags,
                    "is_fork": skill.is_fork, "category": category,
                })
        return list(providers.values())
    
    def get_global_skills(self):
        return [{**asdict(s), 'canonical_path': s.canonical_path} for s in self.global_skills.values() if not s.name.startswith("agency-")]
    
    def get_provider_skills(self, provider):
        result = []
        for skill in self.global_skills.values():
            for p in skill.providers:
                if p['name'] == provider:
                    result.append({
                        "global_id": skill.id, "name": skill.name,
                        "description": skill.description, "enabled": p['enabled'],
                        "tags": skill.tags, "is_fork": skill.is_fork,
                        "canonical_path": skill.canonical_path
                    })
                    break
        return result
    
    def get_skill_by_name(self, name):
        for s in self.global_skills.values():
            if s.name == name: return s
        return None
    
    def toggle_provider_skill(self, provider, skill_name, enabled):
        key = f"{provider}.{skill_name}"
        if key in self.provider_index:
            gid = self.provider_index[key]
            skill = self.global_skills[gid]
            for p in skill.providers:
                if p['name'] == provider:
                    p['enabled'] = enabled; self.save(); return True
        for s in self.global_skills.values():
            if s.name == skill_name and s.is_fork:
                for p in s.providers:
                    if p['name'] == provider:
                        p['enabled'] = enabled; self.save(); return True
        return False
    
    def delete_provider_skill(self, provider, skill_name):
        key = f"{provider}.{skill_name}"
        if key in self.provider_index:
            gid = self.provider_index[key]
            skill = self.global_skills[gid]
            skill.providers = [p for p in skill.providers if p['name'] != provider]
            del self.provider_index[key]
            self.save()
            return True
        for s in self.global_skills.values():
            if s.name == skill_name:
                for p in s.providers:
                    if p['name'] == provider:
                        s.providers = [pp for pp in s.providers if pp['name'] != provider]
                        self.save()
                        return True
        return False
    
    def delete_global_skill(self, skill_name):
        for gid, skill in list(self.global_skills.items()):
            if skill.name == skill_name and not skill.is_fork:
                canon = Path(skill.canonical_path)
                # 1. Eliminar symlinks PRIMERO
                for provider, src_dir in self.PROVIDER_SOURCES.items():
                    if not src_dir.exists(): continue
                    link = src_dir / skill_name
                    if link.exists() and link.is_symlink():
                        try:
                            if str(link.resolve()) == skill.canonical_path:
                                link.unlink()
                        except: pass
                # 2. Eliminar directorio canónico
                if canon.exists():
                    shutil.rmtree(canon)
                keys = [k for k, v in self.provider_index.items() if v == gid]
                for k in keys: del self.provider_index[k]
                del self.global_skills[gid]
                self.save()
                return True
        return False

_registry = None
def get_registry():
    global _registry
    if _registry is None:
        _registry = SimpleSkillRegistry()
    return _registry

print("✅ SimpleSkillRegistry listo")

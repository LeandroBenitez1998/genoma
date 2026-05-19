"use client";
import { api, fetchSkillProviders } from '@/lib/api';

import { useState, useEffect } from "react";
import { Sparkles, ToggleLeft, ToggleRight, Search, RefreshCw } from "lucide-react";

interface Skill {
  name: string;
  description: string;
  enabled: boolean;
  tags: string[];
  is_fork?: boolean;
  category?: string;
}

interface Provider {
  name: string;
  total: number;
  enabled: number;
  skills: Skill[];
  path?: string;
}

export default function SkillsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterProvider, setFilterProvider] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [deleteTarget, setDeleteTarget] = useState<{provider: string, skill: string} | null>(null);

  const fetchSkills = async () => {
    setLoading(true);
    try {
      const data = await fetchSkillProviders();
      if (data.status === "ok") {
        setProviders(data.providers);
      }
    } catch (error) {
      console.error("Error fetching skills:", error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchSkills();
  }, []);


  const handleDeleteSkill = async (provider: string, skillName: string, isGlobal: boolean = false) => {
    if (!confirm(`¿Eliminar ${isGlobal ? "GLOBALMENTE" : "de "+provider} la skill "${skillName}"?`)) return;
    
    try {
      const endpoint = isGlobal 
        ? `/api/skills/global/${encodeURIComponent(skillName)}`
        : `/api/skills/${provider}/${encodeURIComponent(skillName)}`;
      
      const res = await api<{status:string; message?:string}>(endpoint, {
        method: "DELETE",
      });
      
      if (res.status === "ok") {
        fetchSkills();
      } else {
        alert("Error: " + (res.message || "unknown"));
      }
    } catch (error) {
      console.error("Delete error:", error);
      alert("Error eliminando skill");
    }
  };

  const toggleSkill = async (provider: string, skillName: string, enabled: boolean) => {
    try {
      await api<{status:string}>("/api/skills/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, skill_name: skillName, enabled }),
      });
      // Actualizar localmente
      setProviders(prev => prev.map(p => {
        if (p.name !== provider) return p;
        return {
          ...p,
          skills: p.skills.map(s =>
            s.name === skillName ? { ...s, enabled } : s
          ),
          enabled: p.skills.filter(s =>
            (s.name === skillName ? enabled : s.enabled)
          ).length,
        };
      }));
    } catch (error) {
      console.error("Error toggling skill:", error);
    }
  };

  const [filterCategory, setFilterCategory] = useState<string>("all");

  // Extraer categorías únicas
  const allCategories = Array.from(
    new Set(providers.flatMap(p => p.skills.map(s => s.category)))
  ).sort();

  // Filtrar skills por búsqueda y categoría
  const filteredProviders = providers.map(p => ({
    ...p,
    skills: p.skills.filter(s => {
      const q = search.toLowerCase();
      const matchText = 
        s.name.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q);
      const matchProvider = filterProvider === "all" || p.name === filterProvider;
      const matchStatus = filterStatus === "all" || 
        (filterStatus === "enabled" && s.enabled) ||
        (filterStatus === "disabled" && !s.enabled);
      const matchCategory = filterCategory === "all" || s.category === filterCategory;
      return matchText && matchProvider && matchStatus && matchCategory;
    }),
  })).filter(p => p.skills.length > 0);

  const providerIcons: Record<string, string> = {
    "claude-code": "🤖",
    "opencode": "💻",
    "kilocode": "⚡",
    "antigravity": "🚀",
    "hermes": "🪽",
  };

  const providerColors: Record<string, string> = {
    "claude-code": "bg-orange-500/10 border-orange-500/30 text-orange-400",
    "opencode": "bg-blue-500/10 border-blue-500/30 text-blue-400",
    "kilocode": "bg-yellow-500/10 border-yellow-500/30 text-yellow-400",
    "antigravity": "bg-purple-500/10 border-purple-500/30 text-purple-400",
    "hermes": "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-purple-400" />
            <div>
              <h1 className="text-3xl font-bold">Skill Hub</h1>
              <p className="text-gray-400 text-sm">
                Gestiona tus skills de todos los proveedores
              </p>
            </div>
          </div>
          <button
            onClick={fetchSkills}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Search & Filters */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input
            type="text"
            placeholder="Buscar skills por nombre, proveedor o descripción..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-gray-900 border border-gray-800 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
        </div>

        {/* Category & Provider Filters */}
        <div className="flex flex-wrap gap-3 mb-6">
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">📁 Todas las categorías</option>
            {allCategories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          
          <select
            value={filterProvider}
            onChange={(e) => setFilterProvider(e.target.value)}
            className="px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">🔧 Todos los providers</option>
            {providers.map(p => (
              <option key={p.name} value={p.name}>{p.name}</option>
            ))}
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="all">⚡ Todos los estados</option>
            <option value="enabled">✅ Activas</option>
            <option value="disabled">❌ Desactivadas</option>
          </select>

          {(filterCategory !== "all" || filterProvider !== "all" || filterStatus !== "all" || search) && (
            <button
              onClick={() => { setFilterCategory("all"); setFilterProvider("all"); setFilterStatus("all"); setSearch(""); }}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm text-gray-400 transition-colors"
            >
              Limpiar filtros
            </button>
          )}
        </div>

        {/* Stats */}
        {!loading && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            {providers.map(p => (
              <div
                key={p.name}
                className={`p-4 rounded-lg border ${providerColors[p.name] || "bg-gray-800 border-gray-700"}`}
              >
                <div className="text-2xl mb-1">{providerIcons[p.name] || "🔧"}</div>
                <div className="text-sm font-medium capitalize">{p.name}</div>
                <div className="text-2xl font-bold">{p.enabled}/{p.total}</div>
                <div className="text-xs opacity-70">habilitadas</div>
              </div>
            ))}
          </div>
        )}

        {/* Skills por proveedor */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-purple-400" />
            <span className="ml-3">Escaneando skills...</span>
          </div>
        ) : (
          <div className="space-y-8">
            {filteredProviders.map(provider => (
              <div key={provider.name} className="bg-gray-900/50 rounded-xl border border-gray-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{providerIcons[provider.name] || "🔧"}</span>
                    <div>
                      <h2 className="text-xl font-bold capitalize flex items-center gap-2">
                        {provider.name}
                        <span className="text-sm font-normal text-gray-500">
                          ({provider.enabled}/{provider.total} activas)
                        </span>
                      </h2>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-800 text-gray-400 border border-gray-700">
                      {provider.total} skills
                    </span>
                  </div>
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  {provider.skills
                    .filter(skill => {
                      const q = search.toLowerCase();
                      const matchText = 
                        skill.name.toLowerCase().includes(q) ||
                        skill.description.toLowerCase().includes(q) ||
                        skill.tags.some(t => t.toLowerCase().includes(q));
                      const matchProvider = filterProvider === "all" || provider.name === filterProvider;
                      const matchStatus = filterStatus === "all" || 
                        (filterStatus === "enabled" && skill.enabled) ||
                        (filterStatus === "disabled" && !skill.enabled);
                      return matchText && matchProvider && matchStatus;
                    })
                    .map(skill => (
                    <div
                      key={`${provider.name}-${skill.name}`}
                      className="p-4 bg-gray-800/50 rounded-lg border border-gray-700/50 hover:border-gray-600 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium text-gray-100 truncate">
                              {skill.name}
                            </h3>
                            {skill.is_fork && (
                              <span className="px-1.5 py-0.5 text-xs bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 rounded">
                                FORK
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-400 line-clamp-2">
                            {skill.description}
                          </p>
                          {skill.tags.length > 0 && (
                            <div className="flex gap-1 mt-2 flex-wrap">
                              {skill.tags.slice(0, 4).map(tag => (
                                <span key={tag} className="px-2 py-0.5 text-xs bg-gray-700 text-gray-300 rounded">
                                  {tag}
                                </span>
                              ))}
                              {skill.tags.length > 4 && (
                                <span className="px-2 py-0.5 text-xs bg-gray-700 text-gray-300 rounded">
                                  +{skill.tags.length - 4}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <button
                            onClick={() => toggleSkill(provider.name, skill.name, !skill.enabled)}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                              skill.enabled
                                ? "bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20"
                                : "bg-gray-700 text-gray-300 border border-gray-600 hover:bg-gray-600"
                            }`}
                            title={skill.enabled ? "Desactivar" : "Activar"}
                          >
                            {skill.enabled ? (
                              <><ToggleRight className="w-4 h-4" /> Activada</>
                            ) : (
                              <><ToggleLeft className="w-4 h-4" /> Desactivada</>
                            )}
                          </button>
                          <button
                            onClick={() => handleDeleteSkill(provider.name, skill.name, false)}
                            className="px-3 py-1.5 rounded-lg text-sm font-medium bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors"
                            title="Eliminar de este provider"
                          >
                            🗑️ Quitar
                          </button>
                          {!skill.is_fork && (
                            <button
                              onClick={() => handleDeleteSkill(provider.name, skill.name, true)}
                              className="px-3 py-1.5 rounded-lg text-sm font-medium bg-orange-500/10 text-orange-400 border border-orange-500/20 hover:bg-orange-500/20 transition-colors"
                              title="Eliminar skill globalmente"
                            >
                              🗑️💥 Eliminar Global
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {!loading && filteredProviders.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No se encontraron skills. Instala skills en los directorios:
                <pre className="mt-2 p-4 bg-gray-900 rounded text-xs text-left overflow-auto">
                  {`~/.claude/skills/
~/.opencode/skills/
~/.kilocode/skills/
~/.antigravity/providers/
~/.hermes/skills/`}
                </pre>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}

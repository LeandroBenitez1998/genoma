"use client";

import { useState, useEffect, useMemo } from "react";
import { Sparkles, ToggleLeft, ToggleRight, Search, RefreshCw, FolderOpen, ChevronDown, ChevronRight } from "lucide-react";
import { api } from '@/lib/api';

interface Skill {
  name: string;
  description: string;
  enabled: boolean;
  tags: string[];
  category?: string;
  is_fork?: boolean;
}

interface Provider {
  name: string;
  total: number;
  enabled: number;
  skills: Skill[];
}

export default function SkillsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [expandedProviders, setExpandedProviders] = useState<Set<string>>(new Set());
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedProvider, setSelectedProvider] = useState<string>("all");
  const [visibleCounts, setVisibleCounts] = useState<Record<string, number>>({});

  const fetchSkills = async () => {
    setLoading(true);
    try {
      const data = await api<{status: string; providers: Provider[]}>('/api/skills/providers');
      if (data.status === "ok") {
        setProviders(data.providers);
        const allNames = new Set(data.providers.map(p => p.name));
        setExpandedProviders(allNames);
      }
    } catch (error) {
      console.error("Error fetching skills:", error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchSkills();
  }, []);

  const toggleSkill = async (provider: string, skillName: string, enabled: boolean) => {
    try {
      await api<{status:string}>("/api/skills/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, skill_name: skillName, enabled }),
      });
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

  const allCategories = useMemo(() => {
    const cats = new Set<string>();
    providers.forEach(p => p.skills.forEach(s => {
      if (s.category) cats.add(s.category);
    }));
    return Array.from(cats).sort();
  }, [providers]);

  const filteredProviders = useMemo(() => {
    let result = providers;
    if (selectedProvider !== "all") {
      result = result.filter(p => p.name === selectedProvider);
    }
    return result.map(p => ({
      ...p,
      skills: p.skills.filter(s => {
        const matchesSearch = !search ||
          s.name.toLowerCase().includes(search.toLowerCase()) ||
          (s.description || "").toLowerCase().includes(search.toLowerCase()) ||
          (s.category || "").toLowerCase().includes(search.toLowerCase());
        const matchesCategory = selectedCategory === "all" || s.category === selectedCategory;
        return matchesSearch && matchesCategory;
      }),
    })).filter(p => p.skills.length > 0);
  }, [providers, search, selectedCategory, selectedProvider]);

  const getSkillsByCategory = (skills: Skill[]) => {
    const groups: Record<string, Skill[]> = {};
    skills.forEach(s => {
      const cat = s.category || "uncategorized";
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(s);
    });
    return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b));
  };

  const toggleProvider = (name: string) => {
    setExpandedProviders(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const toggleCategory = (key: string) => {
    setExpandedCategories(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const getVisibleCount = (key: string, total: number) => {
    return visibleCounts[key] || Math.min(30, total);
  };

  const showMore = (key: string, total: number) => {
    setVisibleCounts(prev => ({
      ...prev,
      [key]: Math.min((prev[key] || 30) + 30, total)
    }));
  };

  const providerIcons: Record<string, string> = {
    "claude-code": "🤖",
    "opencode": "💻",
    "kilocode": "⚡",
    "antigravity": "🚀",
    "hermes": "🪽",
    "agency": "🏢",
  };

  return (
    <div className="min-h-screen bg-[var(--evo-bg-base)] text-[var(--evo-text-primary)] p-6 transition-colors duration-300">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[var(--evo-primary-100)] flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-[var(--evo-primary-700)]" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-[var(--evo-text-primary)]">Skill Hub</h1>
              <p className="text-[var(--evo-text-secondary)] text-sm">
                Tus skills locales, organizadas por proveedor y categoría
              </p>
            </div>
          </div>
          <button
            onClick={fetchSkills}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--evo-bg-surface)] border border-gray-200 dark:border-gray-700 text-[var(--evo-text-secondary)] hover:bg-[var(--evo-bg-surface-hover)] rounded-xl transition-all shadow-[var(--evo-shadow-sm)]"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Search + Filters */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--evo-text-tertiary)]" />
            <input
              type="text"
              placeholder="Buscar skills por nombre, descripción o categoría..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-[var(--evo-bg-surface)] border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-[var(--evo-primary-500)]/30 text-[var(--evo-text-primary)] shadow-[var(--evo-shadow-sm)] placeholder:text-[var(--evo-text-tertiary)]"
            />
          </div>
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="px-4 py-3 bg-[var(--evo-bg-surface)] border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-[var(--evo-primary-500)]/30 text-[var(--evo-text-secondary)] shadow-[var(--evo-shadow-sm)]"
          >
            <option value="all">Todos los providers</option>
            {providers.map(p => (
              <option key={p.name} value={p.name}>{p.name}</option>
            ))}
          </select>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-3 bg-[var(--evo-bg-surface)] border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-[var(--evo-primary-500)]/30 text-[var(--evo-text-secondary)] shadow-[var(--evo-shadow-sm)]"
          >
            <option value="all">Todas las categorías</option>
            {allCategories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>

        {/* Stats */}
        {!loading && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            {providers.map(p => (
              <div
                key={p.name}
                className="p-5 rounded-2xl border border-gray-100 dark:border-gray-800 bg-[var(--evo-bg-surface)] shadow-[var(--evo-shadow-md)] hover:shadow-[var(--evo-shadow-lg)] transition-shadow"
              >
                <div className="text-2xl mb-2">{providerIcons[p.name] || "🔧"}</div>
                <div className="text-sm font-medium text-[var(--evo-text-secondary)] capitalize">{p.name}</div>
                <div className="text-3xl font-bold text-[var(--evo-primary-700)] mt-1">{p.enabled}/{p.total}</div>
                <div className="text-xs text-[var(--evo-text-tertiary)] mt-1">habilitadas</div>
              </div>
            ))}
          </div>
        )}

        {/* Skills por proveedor → categoría */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-[var(--evo-primary-500)]" />
            <span className="ml-3 text-[var(--evo-text-secondary)]">Escaneando skills...</span>
          </div>
        ) : (
          <div className="space-y-6">
            {filteredProviders.map(provider => (
              <div key={provider.name} className="bg-[var(--evo-bg-surface)] rounded-2xl border border-gray-100 dark:border-gray-800 shadow-[var(--evo-shadow-md)] overflow-hidden">
                {/* Provider Header */}
                <button
                  onClick={() => toggleProvider(provider.name)}
                  className="w-full flex items-center justify-between p-5 hover:bg-[var(--evo-bg-surface-hover)] transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{providerIcons[provider.name] || "🔧"}</span>
                    <div className="text-left">
                      <h2 className="text-lg font-bold capitalize flex items-center gap-2 text-[var(--evo-text-primary)]">
                        {provider.name}
                        <span className="text-sm font-normal text-[var(--evo-text-tertiary)]">
                          ({provider.enabled}/{provider.total} activas)
                        </span>
                      </h2>
                      <p className="text-xs text-[var(--evo-text-tertiary)]">
                        {getSkillsByCategory(provider.skills).length} categorías
                      </p>
                    </div>
                  </div>
                  {expandedProviders.has(provider.name) ? (
                    <ChevronDown className="w-5 h-5 text-[var(--evo-text-tertiary)]" />
                  ) : (
                    <ChevronRight className="w-5 h-5 text-[var(--evo-text-tertiary)]" />
                  )}
                </button>

                {/* Provider Content */}
                {expandedProviders.has(provider.name) && (
                  <div className="px-5 pb-5 space-y-4">
                    {getSkillsByCategory(provider.skills).map(([category, skills]) => {
                      const catKey = `${provider.name}::${category}`;
                      const isExpanded = expandedCategories.has(catKey);
                      return (
                        <div key={catKey} className="border border-gray-100 dark:border-gray-800 rounded-xl overflow-hidden">
                          {/* Category Header */}
                          <button
                            onClick={() => toggleCategory(catKey)}
                            className="w-full flex items-center justify-between p-3 hover:bg-[var(--evo-bg-base)] transition-colors"
                          >
                            <div className="flex items-center gap-2">
                              <FolderOpen className="w-4 h-4 text-[var(--evo-text-tertiary)]" />
                              <span className="text-sm font-semibold capitalize px-2 py-0.5 rounded-lg border bg-[var(--evo-primary-50)] text-[var(--evo-primary-700)] border-[var(--evo-primary-200)]">
                                {category}
                              </span>
                              <span className="text-xs text-[var(--evo-text-tertiary)]">
                                {skills.length} skills
                              </span>
                            </div>
                            {isExpanded ? (
                              <ChevronDown className="w-4 h-4 text-[var(--evo-text-tertiary)]" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-[var(--evo-text-tertiary)]" />
                            )}
                          </button>

                          {/* Skills Grid */}
                          {isExpanded && (
                            <div className="p-3 pt-0">
                              <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
                                {skills.slice(0, getVisibleCount(catKey, skills.length)).map(skill => (
                                  <div
                                    key={skill.name}
                                    className="p-3 bg-[var(--evo-bg-base)] rounded-lg border border-gray-100 dark:border-gray-800 hover:border-[var(--evo-primary-300)] hover:shadow-[var(--evo-shadow-sm)] transition-all"
                                  >
                                    <div className="flex items-start justify-between gap-3">
                                      <div className="flex-1 min-w-0">
                                        <h3 className="font-medium text-[var(--evo-text-primary)] text-sm truncate">
                                          {skill.name}
                                        </h3>
                                        <p className="text-xs text-[var(--evo-text-secondary)] mt-1 line-clamp-2">
                                          {skill.description || "Sin descripción"}
                                        </p>
                                        {skill.tags && skill.tags.length > 0 && (
                                          <div className="flex gap-1 mt-2 flex-wrap">
                                            {skill.tags.map(tag => (
                                              <span
                                                key={tag}
                                                className="px-1.5 py-0.5 text-[10px] bg-[var(--evo-bg-surface-hover)] text-[var(--evo-text-secondary)] rounded"
                                              >
                                                {tag}
                                              </span>
                                            ))}
                                          </div>
                                        )}
                                      </div>
                                      <button
                                        onClick={() => toggleSkill(provider.name, skill.name, !skill.enabled)}
                                        className={`flex-shrink-0 p-1.5 rounded-lg transition-colors ${
                                          skill.enabled
                                            ? "bg-[var(--evo-success)]/10 text-[var(--evo-success)] hover:bg-[var(--evo-success)]/20"
                                            : "bg-gray-100 dark:bg-gray-800 text-[var(--evo-text-tertiary)] hover:bg-gray-200 dark:hover:bg-gray-700"
                                        }`}
                                        title={skill.enabled ? "Desactivar" : "Activar"}
                                      >
                                        {skill.enabled ? (
                                          <ToggleRight className="w-5 h-5" />
                                        ) : (
                                          <ToggleLeft className="w-5 h-5" />
                                        )}
                                      </button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                              {skills.length > getVisibleCount(catKey, skills.length) && (
                                <button
                                  onClick={() => showMore(catKey, skills.length)}
                                  className="w-full mt-3 py-2 text-sm text-[var(--evo-primary-600)] hover:text-[var(--evo-primary-700)] hover:bg-[var(--evo-primary-50)] rounded-lg transition-colors border border-dashed border-[var(--evo-primary-300)]"
                                >
                                  Mostrar más ({skills.length - getVisibleCount(catKey, skills.length)} restantes)
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {!loading && filteredProviders.length === 0 && (
          <div className="text-center py-12 text-[var(--evo-text-tertiary)]">
            No se encontraron skills. Instala skills en los directorios:
            <pre className="mt-2 p-4 bg-[var(--evo-bg-surface)] rounded-xl text-xs text-left overflow-auto border border-gray-100 dark:border-gray-800">
{`~/.claude/skills/
~/.opencode/skills/
~/.kilocode/skills/
~/.antigravity/providers/
~/.hermes/skills/`}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

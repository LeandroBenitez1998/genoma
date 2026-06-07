import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchSkills,
  fetchSkill,
  fetchSkillHistory,
  refreshSkills,
  type SkillInfo,
  type SkillDetail,
  type EvolutionRun,
} from '@/lib/api';

export function useSkills() {
  return useQuery<SkillInfo[]>({
    queryKey: ['skills'],
    queryFn: fetchSkills,
    staleTime: 60_000,
  });
}

export function useSkill(name: string) {
  return useQuery<SkillDetail>({
    queryKey: ['skill', name],
    queryFn: () => fetchSkill(name),
    enabled: !!name,
  });
}

export function useSkillHistory(name: string) {
  return useQuery<EvolutionRun[]>({
    queryKey: ['skill-history', name],
    queryFn: () => fetchSkillHistory(name),
    enabled: !!name,
  });
}

export function useRefreshSkills() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: refreshSkills,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills'] });
    },
  });
}

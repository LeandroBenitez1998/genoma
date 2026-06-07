import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchJobs,
  fetchJob,
  fetchJobLogs,
  cancelJob,
  startEvolution,
  type EvolutionJob,
} from '@/lib/api';

export function useJobs(activeOnly = false) {
  return useQuery<EvolutionJob[]>({
    queryKey: ['jobs', { activeOnly }],
    queryFn: () => fetchJobs(activeOnly),
    refetchInterval: 5_000,
  });
}

export function useJob(jobId: string) {
  return useQuery<EvolutionJob>({
    queryKey: ['job', jobId],
    queryFn: () => fetchJob(jobId),
    enabled: !!jobId,
    refetchInterval: 5_000,
  });
}

export function useJobLogs(jobId: string, since = 0) {
  return useQuery({
    queryKey: ['job-logs', jobId, since],
    queryFn: () => fetchJobLogs(jobId, since),
    enabled: !!jobId,
    refetchInterval: 3_000,
  });
}

export function useCancelJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => cancelJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useStartEvolution() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ skillName, iterations }: { skillName: string; iterations: number }) =>
      startEvolution(skillName, iterations),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['skill-history'] });
    },
  });
}

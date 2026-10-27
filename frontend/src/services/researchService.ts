import { apiClient } from './api';
import { BenchmarkData } from '../types/changes';

export const researchService = {
  async getBenchmarks(): Promise<BenchmarkData> {
    const res = await apiClient.get<BenchmarkData>('/research/benchmarks');
    return res.data;
  },
};

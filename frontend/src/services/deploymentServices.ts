import api from "../lib/axios";
import type { Deployment } from "../types/Deployment";

export const getDeployment = async (): Promise<Deployment> => {
  const response = await api.get<Deployment>("/deployment");
  return response.data;
};

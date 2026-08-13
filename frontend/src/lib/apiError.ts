import { isAxiosError } from "axios";

export type ValidationDetail = {
  loc: (string | number)[];
  msg: string;
};

type ApiErrorBody = {
  detail?: string | ValidationDetail[];
  error?: {
    code?: string;
    message?: string;
    details?: ValidationDetail[];
  };
};

const bodyFrom = (error: unknown): ApiErrorBody | undefined => {
  if (!isAxiosError(error)) {
    return undefined;
  }
  return error.response?.data as ApiErrorBody | undefined;
};

export const getApiErrorCode = (error: unknown): string | undefined => {
  const data = bodyFrom(error);
  if (typeof data?.error?.code === "string") {
    return data.error.code;
  }
  if (typeof data?.detail === "string") {
    return data.detail;
  }
  return undefined;
};

export const getApiErrorMessage = (error: unknown, fallback: string): string => {
  const data = bodyFrom(error);
  const details = Array.isArray(data?.error?.details)
    ? data.error.details
    : Array.isArray(data?.detail)
      ? data.detail
      : null;
  if (details) {
    return details
      .map((item) => {
        const field = String(item.loc[item.loc.length - 1] ?? "field");
        return `${field}: ${item.msg}`;
      })
      .join(" · ");
  }
  if (typeof data?.error?.message === "string" && data.error.message.length > 0) {
    return data.error.message;
  }
  if (typeof data?.detail === "string") {
    return data.detail;
  }
  return fallback;
};

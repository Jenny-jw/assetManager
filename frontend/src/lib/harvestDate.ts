export function harvestIntToDateInput(
  value: string | number | undefined,
): string {
  if (value == null || value === "") return "";
  const digits = String(value).trim();
  if (digits.length !== 8) return "";
  return `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`;
}

export function dateInputToHarvestInt(value: string): string {
  if (!value) return "";
  return value.replace(/-/g, "");
}

export function isHarvestYyyymmdd(value: number): boolean {
  if (!Number.isInteger(value) || value < 20100101 || value > 22001231) {
    return false;
  }
  const text = String(value);
  if (text.length !== 8) return false;
  const year = Number(text.slice(0, 4));
  const month = Number(text.slice(4, 6));
  const day = Number(text.slice(6, 8));
  const date = new Date(Date.UTC(year, month - 1, day));
  return (
    date.getUTCFullYear() === year &&
    date.getUTCMonth() === month - 1 &&
    date.getUTCDate() === day
  );
}

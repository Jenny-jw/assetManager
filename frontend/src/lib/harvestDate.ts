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

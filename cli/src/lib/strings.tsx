export const isPositiveInteger = (value: string | undefined): boolean =>
  value !== undefined && /^[1-9]\d*$/.test(value)

export const hyperlink = (text: string, url: string) =>
  `\u001B]8;;${url}\u0007${text}\u001B]8;;\u0007`

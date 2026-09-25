export const hyperlink = (text: string, url: string) =>
  `\u001B]8;;${url}\u0007${text}\u001B]8;;\u0007`

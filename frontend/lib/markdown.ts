export function normalizeMarkdown(md: string): string {
  return md
    .replace(/\r\n?/g, "\n")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")        // drop
    .replace(/\[([^\]]*)\]\(\s*\)/g, "$1")       // empty links -> plain text
    .replace(/^\s*[-*]\s*$/gm, "")               // empty bullets
    .replace(/^\s*[-=_*]{3,}\s*$/gm, "---")      // unify horizontal rules
    .split("\n")
    .map((line) => line.replace(/[ \t]+/g, " ").trimEnd()) // collapse inline whitespace
    .join("\n")
    .replace(/\n{3,}/g, "\n\n")                  // max one blank line
    .trim();
}
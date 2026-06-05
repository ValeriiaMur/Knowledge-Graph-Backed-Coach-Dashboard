import type { ReactNode } from "react";

/**
 * Minimal, dependency-free Markdown renderer for LLM output. Covers the
 * constructs the copilot and composer actually emit: headings, bold / italic /
 * inline code, links, ordered + unordered lists, GFM pipe tables, blockquotes,
 * and horizontal rules. Builds React nodes (never dangerouslySetInnerHTML), so
 * text stays escaped and link hrefs are sanitized to http(s)/mailto.
 *
 * Deliberately does NOT treat `_underscore_` as emphasis: node ids like
 * `weekly_completion_pct` and `joint:knee` are common in this domain and would
 * be mangled. The copilot uses `*`/`**` for emphasis anyway.
 */

type Props = { children: string; inline?: boolean; className?: string };

// bold | italic | code | [label](url)
const INLINE = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;

function safeHref(url: string): string | undefined {
  return /^(https?:|mailto:)/i.test(url) ? url : undefined;
}

function renderInline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  let key = 0;
  INLINE.lastIndex = 0;
  let m: RegExpExecArray | null;
  while ((m = INLINE.exec(text)) !== null) {
    const tok = m[0];
    if (m.index > last) out.push(text.slice(last, m.index));
    if (tok.startsWith("**")) {
      out.push(<strong key={key++}>{tok.slice(2, -2)}</strong>);
    } else if (tok.startsWith("`")) {
      out.push(<code key={key++}>{tok.slice(1, -1)}</code>);
    } else if (tok.startsWith("[")) {
      const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(tok);
      const label = link?.[1] ?? tok;
      const href = safeHref(link?.[2] ?? "");
      out.push(
        href ? (
          <a key={key++} href={href} target="_blank" rel="noreferrer">
            {label}
          </a>
        ) : (
          label
        ),
      );
    } else {
      out.push(<em key={key++}>{tok.slice(1, -1)}</em>);
    }
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

function splitRow(row: string): string[] {
  return row
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((c) => c.trim());
}

function isBlockStart(line: string): boolean {
  return /^(#{1,6}\s|\s*[-*+]\s|\s*\d+\.\s|>\s?|\*{3,}\s*$|-{3,}\s*$|_{3,}\s*$)/.test(line);
}

function renderBlocks(src: string): ReactNode[] {
  const lines = src.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i] ?? "";
    if (line.trim() === "") {
      i++;
      continue;
    }

    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    if (heading) {
      const level = heading[1]?.length ?? 1;
      blocks.push(
        <div key={key++} className={`md-h md-h${level}`}>
          {renderInline(heading[2] ?? "")}
        </div>,
      );
      i++;
      continue;
    }

    // GFM table: a header row followed by a |---|---| separator
    const sep = lines[i + 1] ?? "";
    if (line.includes("|") && /^\s*\|?[\s:|-]*-[\s:|-]*$/.test(sep) && sep.includes("-")) {
      const header = splitRow(line);
      i += 2; // skip header + separator
      const rows: string[][] = [];
      while (i < lines.length && (lines[i] ?? "").includes("|")) {
        rows.push(splitRow(lines[i] ?? ""));
        i++;
      }
      blocks.push(
        <table key={key++} className="md-table">
          <thead>
            <tr>
              {header.map((h, c) => (
                <th key={c}>{renderInline(h)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((cells, r) => (
              <tr key={r}>
                {header.map((_, c) => (
                  <td key={c}>{renderInline(cells[c] ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>,
      );
      continue;
    }

    if (/^(\*{3,}|-{3,}|_{3,})\s*$/.test(line.trim())) {
      blocks.push(<hr key={key++} className="md-hr" />);
      i++;
      continue;
    }

    if (/^>\s?/.test(line)) {
      const quote: string[] = [];
      while (i < lines.length && /^>\s?/.test(lines[i] ?? "")) {
        quote.push((lines[i] ?? "").replace(/^>\s?/, ""));
        i++;
      }
      blocks.push(
        <blockquote key={key++} className="md-quote">
          {renderInline(quote.join(" "))}
        </blockquote>,
      );
      continue;
    }

    if (/^\s*[-*+]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i] ?? "")) {
        items.push((lines[i] ?? "").replace(/^\s*[-*+]\s+/, ""));
        i++;
      }
      blocks.push(
        <ul key={key++} className="md-ul">
          {items.map((it, k) => (
            <li key={k}>{renderInline(it)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i] ?? "")) {
        items.push((lines[i] ?? "").replace(/^\s*\d+\.\s+/, ""));
        i++;
      }
      blocks.push(
        <ol key={key++} className="md-ol">
          {items.map((it, k) => (
            <li key={k}>{renderInline(it)}</li>
          ))}
        </ol>,
      );
      continue;
    }

    const para: string[] = [];
    while (i < lines.length && (lines[i] ?? "").trim() !== "" && !isBlockStart(lines[i] ?? "")) {
      para.push(lines[i] ?? "");
      i++;
    }
    blocks.push(
      <p key={key++} className="md-p">
        {renderInline(para.join(" "))}
      </p>,
    );
  }
  return blocks;
}

export function Markdown({ children, inline, className }: Props): JSX.Element {
  if (inline) {
    return <span className={className}>{renderInline(children)}</span>;
  }
  return <div className={className ? `md ${className}` : "md"}>{renderBlocks(children)}</div>;
}

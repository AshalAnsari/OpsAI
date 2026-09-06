import Link from "next/link";
import type { ReactNode } from "react";

function resolveHref(href: string): string {
  if (href.startsWith("./") || href.endsWith(".md")) {
    const file = href.replace(/^\.\//, "");
    if (file.startsWith("cancellation")) return "/policies/cancellation";
    if (file.startsWith("refund")) return "/policies/refund";
    if (file.startsWith("shipping")) return "/policies/shipping";
    if (file.startsWith("payment")) return "/policies/payment";
    if (file.startsWith("account")) return "/policies/account";
  }
  return href;
}

function inlineFormat(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > last) {
      nodes.push(text.slice(last, match.index));
    }
    const token = match[0];
    if (token.startsWith("**")) {
      nodes.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("`")) {
      nodes.push(
        <code key={key++} className="rounded bg-[var(--paper-deep)] px-1.5 py-0.5 text-[0.9em]">
          {token.slice(1, -1)}
        </code>,
      );
    } else {
      const linkMatch = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      if (linkMatch) {
        const label = linkMatch[1];
        const href = resolveHref(linkMatch[2]);
        const internal = href.startsWith("/");
        nodes.push(
          internal ? (
            <Link key={key++} href={href} className="text-[var(--accent)] underline-offset-2 hover:underline">
              {label}
            </Link>
          ) : (
            <a
              key={key++}
              href={href}
              className="text-[var(--accent)] underline-offset-2 hover:underline"
              target="_blank"
              rel="noreferrer"
            >
              {label}
            </a>
          ),
        );
      }
    }
    last = match.index + token.length;
  }

  if (last < text.length) {
    nodes.push(text.slice(last));
  }
  return nodes;
}

type Block =
  | { type: "h1" | "h2" | "h3"; text: string }
  | { type: "quote"; text: string }
  | { type: "hr" }
  | { type: "p"; text: string }
  | { type: "ul" | "ol"; items: string[] }
  | { type: "table"; headers: string[]; rows: string[][] }
  | { type: "code"; lines: string[] };

function parseBlocks(markdown: string): Block[] {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) {
      i += 1;
      continue;
    }

    if (line.trim() === "---") {
      blocks.push({ type: "hr" });
      i += 1;
      continue;
    }

    if (line.startsWith("# ")) {
      blocks.push({ type: "h1", text: line.slice(2).trim() });
      i += 1;
      continue;
    }
    if (line.startsWith("## ")) {
      blocks.push({ type: "h2", text: line.slice(3).trim() });
      i += 1;
      continue;
    }
    if (line.startsWith("### ")) {
      blocks.push({ type: "h3", text: line.slice(4).trim() });
      i += 1;
      continue;
    }

    if (line.startsWith("> ")) {
      const parts: string[] = [];
      while (i < lines.length && lines[i].startsWith("> ")) {
        parts.push(lines[i].slice(2).trim());
        i += 1;
      }
      blocks.push({ type: "quote", text: parts.join(" ") });
      continue;
    }

    if (line.startsWith("```")) {
      i += 1;
      const codeLines: string[] = [];
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i += 1;
      }
      i += 1;
      blocks.push({ type: "code", lines: codeLines });
      continue;
    }

    if (line.trim().startsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableLines.push(lines[i]);
        i += 1;
      }
      const parseRow = (row: string) =>
        row
          .trim()
          .replace(/^\|/, "")
          .replace(/\|$/, "")
          .split("|")
          .map((cell) => cell.trim());
      const headers = parseRow(tableLines[0] || "");
      const bodyRows = tableLines
        .slice(1)
        .filter((row) => !/^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$/.test(row.trim()))
        .map(parseRow);
      blocks.push({ type: "table", headers, rows: bodyRows });
      continue;
    }

    if (/^[-*] /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*] /.test(lines[i])) {
        items.push(lines[i].replace(/^[-*] /, "").trim());
        i += 1;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    if (/^\d+\. /.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\. /, "").trim());
        i += 1;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    const parts: string[] = [line.trim()];
    i += 1;
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].startsWith("#") &&
      !lines[i].startsWith(">") &&
      !lines[i].startsWith("```") &&
      !lines[i].trim().startsWith("|") &&
      !/^[-*] /.test(lines[i]) &&
      !/^\d+\. /.test(lines[i]) &&
      lines[i].trim() !== "---"
    ) {
      parts.push(lines[i].trim());
      i += 1;
    }
    blocks.push({ type: "p", text: parts.join(" ") });
  }

  return blocks;
}

function Inline({ text }: { text: string }) {
  return <>{inlineFormat(text)}</>;
}

export function MarkdownBody({ markdown }: { markdown: string }) {
  const blocks = parseBlocks(markdown);

  return (
    <div className="policy-prose space-y-4 text-[var(--ink)]">
      {blocks.map((block, index) => {
        switch (block.type) {
          case "h1":
            return (
              <h1 key={index} className="font-display text-4xl leading-tight">
                <Inline text={block.text} />
              </h1>
            );
          case "h2":
            return (
              <h2 key={index} className="font-display pt-4 text-2xl">
                <Inline text={block.text} />
              </h2>
            );
          case "h3":
            return (
              <h3 key={index} className="pt-2 text-lg font-semibold">
                <Inline text={block.text} />
              </h3>
            );
          case "quote":
            return (
              <blockquote
                key={index}
                className="rounded-xl border border-[var(--line)] bg-[var(--paper)] px-4 py-3 text-sm text-[var(--ink-soft)]"
              >
                <Inline text={block.text} />
              </blockquote>
            );
          case "hr":
            return <hr key={index} className="border-[var(--line)]" />;
          case "p":
            return (
              <p key={index} className="leading-relaxed text-[var(--ink-soft)]">
                <Inline text={block.text} />
              </p>
            );
          case "ul":
            return (
              <ul key={index} className="list-disc space-y-1 pl-5 text-[var(--ink-soft)]">
                {block.items.map((item, itemIndex) => (
                  <li key={itemIndex}>
                    <Inline text={item} />
                  </li>
                ))}
              </ul>
            );
          case "ol":
            return (
              <ol key={index} className="list-decimal space-y-1 pl-5 text-[var(--ink-soft)]">
                {block.items.map((item, itemIndex) => (
                  <li key={itemIndex}>
                    <Inline text={item} />
                  </li>
                ))}
              </ol>
            );
          case "code":
            return (
              <pre
                key={index}
                className="overflow-x-auto rounded-xl bg-[var(--ink)] px-4 py-3 text-sm text-[var(--paper)]"
              >
                <code>{block.lines.join("\n")}</code>
              </pre>
            );
          case "table":
            return (
              <div key={index} className="overflow-x-auto rounded-xl border border-[var(--line)]">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-[var(--paper)]">
                    <tr>
                      {block.headers.map((header) => (
                        <th key={header} className="px-3 py-2 font-semibold">
                          <Inline text={header} />
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {block.rows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="border-t border-[var(--line)]">
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex} className="px-3 py-2 text-[var(--ink-soft)]">
                            <Inline text={cell} />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          default:
            return null;
        }
      })}
    </div>
  );
}

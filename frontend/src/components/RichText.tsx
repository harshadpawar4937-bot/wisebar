export function RichText({ text }: { text: string }) {
  const blocks = text.trim().split(/\n\n+/);
  return (
    <div className="space-y-4 text-base leading-relaxed text-ink/80">
      {blocks.map((block, index) => {
        if (block.startsWith("## ")) return <h2 key={index} className="pt-4 font-display text-2xl text-ink">{block.slice(3)}</h2>;
        if (block.startsWith("- ")) {
          return (
            <ul key={index} className="list-disc space-y-1 pl-5">
              {block.split("\n").map((line) => <li key={line}>{line.replace(/^- /, "")}</li>)}
            </ul>
          );
        }
        return <p key={index}>{block}</p>;
      })}
    </div>
  );
}

import { Badge } from "@citetrack/ui/badge";
import { Button } from "@citetrack/ui/button";
import { Input } from "@citetrack/ui/input";
import { cn } from "@citetrack/ui";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/")({ component: Home });

function Home() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-20">
      <Badge variant="outline" className="mb-6">
        Coming soon
      </Badge>

      <h1 className="text-5xl font-bold tracking-tight md:text-6xl">Citetrack AI</h1>

      <p className="mt-4 text-lg text-muted-foreground md:text-xl">
        Track how AI cites your brand across ChatGPT, Claude, Perplexity, Gemini, Grok, and AI
        Overviews.
      </p>

      <div className="mt-10 flex flex-col gap-3 sm:flex-row">
        <Input placeholder="your-brand.com" className="sm:max-w-sm" />
        <Button>Check visibility</Button>
      </div>

      <section className="mt-16 grid gap-6 md:grid-cols-3">
        {[
          { n: "6", label: "AI providers monitored" },
          { n: "8", label: "Diagnostic findings types" },
          { n: "~60s", label: "Full scan turnaround" },
        ].map((stat) => (
          <div
            key={stat.label}
            className={cn(
              "rounded-lg border border-border bg-card p-6",
              "transition-colors hover:bg-muted",
            )}
          >
            <div className="text-3xl font-bold">{stat.n}</div>
            <div className="mt-1 text-sm text-muted-foreground">{stat.label}</div>
          </div>
        ))}
      </section>
    </main>
  );
}

import { useState } from "react";
import type { ReactNode } from "react";
import type { EntityResult, ExtractabilityResult, ShoppingResult } from "@citetrack/api-client";
import { Alert } from "@citetrack/ui/alert";
import { Button } from "@citetrack/ui/button";
import { Card } from "@citetrack/ui/card";
import { Input } from "@citetrack/ui/input";
import { Label } from "@citetrack/ui/label";
import { Skeleton } from "@citetrack/ui/skeleton";
import {
  ExternalLink,
  FileSearch,
  Network,
  Play,
  ShoppingBag,
  Sparkles,
} from "lucide-react";
import { PageHeader } from "../components/page-header";
import {
  useCrawlerSimAnalyzer,
  useEntityAnalysisAnalyzer,
  useExtractabilityAnalyzer,
  useQueryFanoutAnalyzer,
  useShoppingAnalysisAnalyzer,
} from "../lib/analyzers-hooks";

function isValidUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function ResultNotice({ degraded }: { degraded: { reason: string; message: string } | null | undefined }) {
  if (!degraded) {
    return null;
  }
  return <Alert variant="warning">{degraded.message}</Alert>;
}

function ErrorNotice({ error }: { error: Error | null }) {
  if (!error) {
    return null;
  }
  return <Alert variant="error">{error.message}</Alert>;
}

function SectionShell({
  title,
  description,
  icon,
  children,
}: {
  title: string;
  description: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <Card className="border-foreground/10 p-5 ring-1 ring-foreground/10">
      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 text-muted-foreground">{icon}</div>
          <div className="space-y-1">
            <h2 className="text-sm font-medium">{title}</h2>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
        {children}
      </div>
    </Card>
  );
}

function ScoreMiniCard({ title, score, finding }: { title: string; score: number; finding: string }) {
  return (
    <div className="rounded-xl border border-foreground/10 p-4 ring-1 ring-foreground/10">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{title}</p>
        <p className="text-lg font-medium">{Math.round(score)}</p>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{finding}</p>
    </div>
  );
}

function ExtractabilityResultView({ result }: { result: ExtractabilityResult }) {
  return (
    <div className="space-y-4" data-testid="extractability-result">
      <div className="rounded-xl border border-foreground/10 p-4 ring-1 ring-foreground/10">
        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Overall score</p>
        <div className="mt-2 flex items-end gap-2">
          <span className="text-3xl font-medium">{Math.round(result.overall_score)}</span>
          <span className="pb-1 text-sm text-muted-foreground">/100</span>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <ScoreMiniCard title="Summary block" score={result.summary_block.score} finding={result.summary_block.finding} />
        <ScoreMiniCard title="Section integrity" score={result.section_integrity.score} finding={result.section_integrity.finding} />
        <ScoreMiniCard title="Modular content" score={result.modular_content.score} finding={result.modular_content.finding} />
        <ScoreMiniCard title="Schema markup" score={result.schema_markup.score} finding={result.schema_markup.finding} />
        <ScoreMiniCard title="Static content" score={result.static_content.score} finding={result.static_content.finding} />
      </div>
      {result.recommendations.length > 0 ? (
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Recommendations</p>
          <div className="space-y-2">
            {result.recommendations.map((recommendation) => (
              <div key={recommendation} className="rounded-xl border border-foreground/10 px-3 py-2 text-sm ring-1 ring-foreground/10">
                {recommendation}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function CrawlerSimResultView({
  result,
  pending,
}: {
  result: ReturnType<typeof useCrawlerSimAnalyzer>["data"];
  pending: boolean;
}) {
  if (pending && !result) {
    return <Skeleton data-testid="crawler-sim-loading" className="h-32 w-full rounded-xl" />;
  }
  if (!result) {
    return null;
  }
  return (
    <div className="space-y-3" data-testid="crawler-sim-result">
      <div className="grid gap-2">
        {result.results.map((item) => (
          <div key={item.bot} className="grid gap-2 rounded-xl border border-foreground/10 p-3 text-sm ring-1 ring-foreground/10 md:grid-cols-[1.2fr_0.6fr_0.6fr_2fr]">
            <p className="font-medium">{item.bot}</p>
            <p>{item.accessible ? "Accessible" : "Blocked"}</p>
            <p>HTTP {item.status_code}</p>
            <p className="text-muted-foreground">{item.reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function EntityResultView({ result }: { result: EntityResult }) {
  const rows = [
    ["Knowledge Graph", result.knowledge_graph.present, result.knowledge_graph.url],
    ["Wikipedia", result.wikipedia.present, result.wikipedia.url],
    ["Wikidata", result.wikidata.present, result.wikidata.url],
  ] as const;
  return (
    <div className="space-y-4" data-testid="entity-result">
      <div className="rounded-xl border border-foreground/10 p-4 ring-1 ring-foreground/10">
        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Entity clarity score</p>
        <p className="mt-2 text-3xl font-medium">{Math.round(result.entity_clarity_score * 100)}</p>
      </div>
      <div className="space-y-2">
        {rows.map(([label, present, url]) => (
          <div key={label} className="grid gap-2 rounded-xl border border-foreground/10 p-3 text-sm ring-1 ring-foreground/10 md:grid-cols-[1fr_0.7fr_2fr]">
            <p className="font-medium">{label}</p>
            <p>{present ? "Present" : "Missing"}</p>
            {url ? (
              <a className="inline-flex items-center gap-1 text-muted-foreground underline underline-offset-4" href={url} target="_blank" rel="noreferrer">
                {url}
                <ExternalLink className="size-3" />
              </a>
            ) : (
              <p className="text-muted-foreground">No source found</p>
            )}
          </div>
        ))}
      </div>
      {result.recommendations.length > 0 ? (
        <div className="space-y-2">
          {result.recommendations.map((item) => (
            <div key={item} className="rounded-xl border border-foreground/10 px-3 py-2 text-sm ring-1 ring-foreground/10">
              {item}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function ShoppingResultView({ result }: { result: ShoppingResult }) {
  const rows = [
    ["Google Shopping", result.google_shopping.brand_products_found],
    ["Google AI shopping text", result.ai_mode_shopping.brand_in_ai_text],
    ["ChatGPT shopping mention", result.chatgpt_shopping.brand_mentioned],
  ] as const;
  return (
    <div className="space-y-4" data-testid="shopping-result">
      <div className="rounded-xl border border-foreground/10 p-4 ring-1 ring-foreground/10">
        <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Visibility score</p>
        <p className="mt-2 text-3xl font-medium">{Math.round(result.visibility_score * 100)}</p>
      </div>
      <div className="grid gap-2">
        {rows.map(([label, visible]) => (
          <div key={label} className="flex items-center justify-between rounded-xl border border-foreground/10 px-3 py-3 text-sm ring-1 ring-foreground/10">
            <span className="font-medium">{label}</span>
            <span>{visible ? "Visible" : "Missing"}</span>
          </div>
        ))}
      </div>
      {result.recommendations.length > 0 ? (
        <div className="space-y-2">
          {result.recommendations.map((item) => (
            <div key={item} className="rounded-xl border border-foreground/10 px-3 py-2 text-sm ring-1 ring-foreground/10">
              {item}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function ContentAnalysisPage() {
  const [url, setUrl] = useState("");
  const [urlError, setUrlError] = useState<string | null>(null);
  const [fanoutPrompt, setFanoutPrompt] = useState("");
  const [brandDomain, setBrandDomain] = useState("");
  const [fanoutError, setFanoutError] = useState<string | null>(null);
  const [entityBrandName, setEntityBrandName] = useState("");
  const [entityInputError, setEntityInputError] = useState<string | null>(null);
  const [shoppingBrandName, setShoppingBrandName] = useState("");
  const [shoppingInputError, setShoppingInputError] = useState<string | null>(null);

  const extractability = useExtractabilityAnalyzer();
  const crawlerSim = useCrawlerSimAnalyzer();
  const queryFanout = useQueryFanoutAnalyzer();
  const entityAnalysis = useEntityAnalysisAnalyzer();
  const shoppingAnalysis = useShoppingAnalysisAnalyzer();

  async function handleAnalyzeUrl() {
    if (!url.trim()) {
      setUrlError("URL is required");
      return;
    }
    if (!isValidUrl(url.trim())) {
      setUrlError("Enter a valid URL");
      return;
    }
    setUrlError(null);
    await Promise.all([
      extractability.mutateAsync({ url: url.trim() }),
      crawlerSim.mutateAsync({ url: url.trim() }),
    ]);
  }

  async function handleFanout() {
    if (!fanoutPrompt.trim() || !brandDomain.trim()) {
      setFanoutError("Prompt and brand domain are required");
      return;
    }
    setFanoutError(null);
    await queryFanout.mutateAsync({ prompt: fanoutPrompt.trim(), brand_domain: brandDomain.trim() });
  }

  async function handleEntity() {
    if (!entityBrandName.trim()) {
      setEntityInputError("Brand name is required");
      return;
    }
    setEntityInputError(null);
    await entityAnalysis.mutateAsync({ brand_name: entityBrandName.trim() });
  }

  async function handleShopping() {
    if (!shoppingBrandName.trim()) {
      setShoppingInputError("Brand name is required");
      return;
    }
    setShoppingInputError(null);
    await shoppingAnalysis.mutateAsync({ brand_name: shoppingBrandName.trim() });
  }

  return (
    <>
      <PageHeader title="Content Analysis" />
      <main className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-6xl space-y-6">
          <SectionShell
            title="Content extractability + crawler access"
            description="Run a URL through the page reader and bot access simulator. These analyzers only run when you click Analyze."
            icon={<FileSearch className="size-4" />}
          >
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <div className="space-y-2">
                <Label htmlFor="content-analysis-url">URL</Label>
                <Input id="content-analysis-url" placeholder="https://example.com/page" value={url} onChange={(event) => setUrl(event.target.value)} />
              </div>
              <div className="flex items-end">
                <Button onClick={() => { void handleAnalyzeUrl(); }} isLoading={extractability.isPending || crawlerSim.isPending}>
                  <Play className="size-4" />
                  Analyze
                </Button>
              </div>
            </div>
            {urlError ? <Alert variant="error">{urlError}</Alert> : null}
            <ErrorNotice error={extractability.error} />
            <ResultNotice degraded={extractability.data?.degraded} />
            {extractability.isPending && !extractability.data ? <Skeleton className="h-48 w-full rounded-xl" /> : null}
            {extractability.data ? <ExtractabilityResultView result={extractability.data} /> : null}
            <ErrorNotice error={crawlerSim.error} />
            <ResultNotice degraded={crawlerSim.data?.degraded} />
            <CrawlerSimResultView result={crawlerSim.data} pending={crawlerSim.isPending} />
          </SectionShell>

          <SectionShell
            title="Query fan-out"
            description="Generate the hidden sub-queries AI systems would likely fan out behind a single prompt, then see if your domain ranks in the top five results."
            icon={<Network className="size-4" />}
          >
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="fanout-prompt">Prompt</Label>
                <Input id="fanout-prompt" value={fanoutPrompt} onChange={(event) => setFanoutPrompt(event.target.value)} placeholder="best AI visibility tools for agencies" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fanout-domain">Brand domain</Label>
                <Input id="fanout-domain" value={brandDomain} onChange={(event) => setBrandDomain(event.target.value)} placeholder="citetrack.ai" />
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={() => { void handleFanout(); }} isLoading={queryFanout.isPending}>
                <Play className="size-4" />
                Run
              </Button>
            </div>
            {fanoutError ? <Alert variant="error">{fanoutError}</Alert> : null}
            <ErrorNotice error={queryFanout.error} />
            <ResultNotice degraded={queryFanout.data?.degraded} />
            {queryFanout.data ? (
              <div className="space-y-3" data-testid="query-fanout-result">
                <div className="rounded-xl border border-foreground/10 p-4 ring-1 ring-foreground/10">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Coverage</p>
                  <p className="mt-2 text-3xl font-medium">{Math.round(queryFanout.data.coverage * 100)}</p>
                </div>
                <div className="space-y-2">
                  {queryFanout.data.results.map((item) => (
                    <div key={item.sub_query} className="grid gap-2 rounded-xl border border-foreground/10 p-3 text-sm ring-1 ring-foreground/10 md:grid-cols-[2fr_0.8fr_0.8fr]">
                      <p className="font-medium">{item.sub_query}</p>
                      <p>{item.ranked ? "Ranked" : "Missing"}</p>
                      <p>{item.position ?? "—"}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </SectionShell>

          <SectionShell
            title="Brand entity clarity"
            description="Check whether your brand resolves cleanly across major entity systems that AI assistants commonly use."
            icon={<Sparkles className="size-4" />}
          >
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <div className="space-y-2">
                <Label htmlFor="entity-brand">Brand name</Label>
                <Input id="entity-brand" value={entityBrandName} onChange={(event) => setEntityBrandName(event.target.value)} placeholder="Citetrack" />
              </div>
              <div className="flex items-end">
                <Button onClick={() => { void handleEntity(); }} isLoading={entityAnalysis.isPending}>
                  <Play className="size-4" />
                  Run
                </Button>
              </div>
            </div>
            {entityInputError ? <Alert variant="error">{entityInputError}</Alert> : null}
            <ErrorNotice error={entityAnalysis.error} />
            <ResultNotice degraded={entityAnalysis.data?.degraded} />
            {entityAnalysis.data ? <EntityResultView result={entityAnalysis.data} /> : null}
          </SectionShell>

          <SectionShell
            title="AI shopping visibility"
            description="Best-effort view into whether shopping-oriented result sets or assistants can already find the brand."
            icon={<ShoppingBag className="size-4" />}
          >
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <div className="space-y-2">
                <Label htmlFor="shopping-brand">Brand name</Label>
                <Input id="shopping-brand" value={shoppingBrandName} onChange={(event) => setShoppingBrandName(event.target.value)} placeholder="Citetrack" />
              </div>
              <div className="flex items-end">
                <Button onClick={() => { void handleShopping(); }} isLoading={shoppingAnalysis.isPending}>
                  <Play className="size-4" />
                  Run
                </Button>
              </div>
            </div>
            {shoppingInputError ? <Alert variant="error">{shoppingInputError}</Alert> : null}
            <ErrorNotice error={shoppingAnalysis.error} />
            <ResultNotice degraded={shoppingAnalysis.data?.degraded} />
            {shoppingAnalysis.data ? <ShoppingResultView result={shoppingAnalysis.data} /> : null}
          </SectionShell>
        </div>
      </main>
    </>
  );
}

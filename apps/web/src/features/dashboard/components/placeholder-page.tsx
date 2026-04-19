import { PageHeader } from "./page-header";

interface PlaceholderPageProps {
  title: string;
  description?: string;
}

export function PlaceholderPage({ title, description }: PlaceholderPageProps) {
  return (
    <>
      <PageHeader title={title} />
      <main className="flex-1 overflow-auto px-6 py-8">
        <div className="mx-auto max-w-3xl rounded-xl bg-card ring-1 ring-foreground/10 p-8 text-center">
          <h2 className="text-lg font-medium">{title}</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {description ?? "This section is coming soon."}
          </p>
        </div>
      </main>
    </>
  );
}

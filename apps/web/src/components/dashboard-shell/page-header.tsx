import { SidebarTrigger } from "@citetrack/ui/sidebar";
import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  actions?: ReactNode;
}

export function PageHeader({ title, actions }: PageHeaderProps) {
  return (
    <header data-testid="page-header" className="flex h-12 shrink-0 items-center justify-between border-b px-4">
      <div className="flex items-center gap-3">
        <SidebarTrigger className="md:hidden" />
        <h1 data-testid="page-header-title" className="text-sm font-medium">
          {title}
        </h1>
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </header>
  );
}

import { Button } from "@citetrack/ui/button";
import { Check, Copy } from "lucide-react";
import { useState } from "react";

interface CodeSnippetProps {
  code: string;
  language?: string;
}

export function CodeSnippet({ code, language = "javascript" }: CodeSnippetProps) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="relative rounded-lg bg-muted/40 ring-1 ring-foreground/10">
      <div className="flex items-center justify-between border-b px-3 py-1.5">
        <span className="text-xs text-muted-foreground">{language}</span>
        <Button variant="ghost" size="sm" onClick={handleCopy} aria-label="Copy code">
          {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
        </Button>
      </div>
      <pre className="overflow-x-auto p-3 text-xs font-mono leading-relaxed">{code}</pre>
    </div>
  );
}

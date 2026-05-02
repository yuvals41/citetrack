import type { BrandDetail, BrandUpsertInput } from "@citetrack/api-client";
import { Alert } from "@citetrack/ui/alert";
import { Button } from "@citetrack/ui/button";
import { Card } from "@citetrack/ui/card";
import { Input } from "@citetrack/ui/input";
import { Label } from "@citetrack/ui/label";
import { zodResolver } from "@hookform/resolvers/zod";
import { Globe, Plus, Tag, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { type BrandFormValues, brandSchema } from "./schemas";

interface BrandEditorCardProps {
  brand: BrandDetail | null;
  mode: "create" | "edit";
  isSaving: boolean;
  onSave: (input: BrandUpsertInput) => Promise<BrandDetail>;
}

export function BrandEditorCard({ brand, mode, isSaving, onSave }: BrandEditorCardProps) {
  const [aliasInput, setAliasInput] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState(false);

  const initialValues = useMemo<BrandFormValues>(
    () => ({
      name: brand?.name ?? "",
      domain: brand?.domain ?? "",
      aliases: brand?.aliases ?? [],
    }),
    [brand],
  );

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<BrandFormValues>({
    resolver: zodResolver(brandSchema),
    defaultValues: initialValues,
  });

  useEffect(() => {
    reset(initialValues);
    setAliasInput("");
    setSaveError(null);
  }, [initialValues, reset]);

  const aliases = watch("aliases");

  function addAlias() {
    const next = aliasInput.trim();
    if (!next || aliases.includes(next) || aliases.length >= 10) {
      return;
    }
    setValue("aliases", [...aliases, next], {
      shouldDirty: true,
      shouldValidate: true,
    });
    setAliasInput("");
  }

  function removeAlias(alias: string) {
    setValue(
      "aliases",
      aliases.filter((item) => item !== alias),
      { shouldDirty: true, shouldValidate: true },
    );
  }

  const onSubmit = handleSubmit(
    async (values) => {
      setSaveError(null);
      try {
        await onSave(values);
        reset(values);
        setSavedMessage(true);
        window.setTimeout(() => setSavedMessage(false), 2000);
      } catch (error) {
        setSaveError(error instanceof Error ? error.message : "Failed to save brand");
      }
    },
    (formErrors) => {
      const aliasMessage = formErrors.aliases?.message;
      if (aliasMessage) {
        setSaveError(aliasMessage);
      }
    },
  );

  return (
    <Card data-testid="brand-editor-card" className={`p-6 shadow-none ${mode === "create" ? "mx-auto max-w-2xl text-center" : ""}`}>
      <div className={mode === "create" ? "space-y-3" : "space-y-4"}>
        <div className={mode === "create" ? "flex justify-center" : ""}>
          <div className="flex h-11 w-11 items-center justify-center rounded-full ring-1 ring-foreground/10">
            <Tag className="size-5 text-muted-foreground" />
          </div>
        </div>

        {mode === "create" ? (
          <div className="space-y-2">
            <h2 className="text-lg font-medium">No brand set up yet</h2>
            <p className="text-sm text-muted-foreground">
              Add the main brand this workspace tracks so scans, prompts, and reports stay grounded.
            </p>
          </div>
        ) : (
          <div className="space-y-3 text-left">
            <div>
              <p className="text-sm font-medium">Current brand</p>
              <p className="mt-1 text-xl font-medium">{brand?.name}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <span className="inline-flex items-center gap-2 rounded-full px-3 py-1 ring-1 ring-foreground/10">
                <Globe className="size-3.5" />
                {brand?.domain}
              </span>
              {(brand?.aliases ?? []).map((alias) => (
                <span key={alias} className="rounded-full px-3 py-1 ring-1 ring-foreground/10">
                  {alias}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <form
        className={`mt-6 space-y-4 text-left ${mode === "create" ? "max-w-xl mx-auto w-full" : ""}`}
        onSubmit={(event) => {
          void onSubmit(event);
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="brand-name">Name</Label>
                  <Input data-testid="brand-name-input" id="brand-name" {...register("name")} />
          {errors.name ? <p className="text-xs text-destructive">{errors.name.message}</p> : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="brand-domain">Domain</Label>
                  <Input data-testid="brand-domain-input" id="brand-domain" {...register("domain")} />
          {errors.domain ? (
            <p className="text-xs text-destructive">{errors.domain.message}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="brand-alias">Aliases</Label>
          <div className="flex gap-2">
              <Input
                data-testid="brand-alias-input"
                id="brand-alias"
                value={aliasInput}
              onChange={(event) => setAliasInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  addAlias();
                }
              }}
              placeholder="Type an alias and press Enter"
            />
              <Button
                data-testid="brand-alias-add-button"
                type="button"
                variant="outline"
                onClick={addAlias}
              disabled={!aliasInput.trim() || aliases.length >= 10}
            >
              <Plus className="size-4" />
              Add
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {aliases.map((alias) => (
              <span
                key={alias}
                className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm ring-1 ring-foreground/10"
              >
                {alias}
                <button
                  type="button"
                  data-testid={`brand-alias-remove-${alias}`}
                  aria-label={`Remove alias ${alias}`}
                  onClick={() => removeAlias(alias)}
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  <X className="size-3.5" />
                </button>
              </span>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Up to 10 aliases. Use short names people mention in AI responses.
          </p>
          {errors.aliases ? (
            <p className="text-xs text-destructive">{errors.aliases.message}</p>
          ) : null}
        </div>

        {saveError ? <Alert variant="error">{saveError}</Alert> : null}

        <div className="flex items-center gap-3">
            <Button
              data-testid="brand-save-button"
              type="submit"
              disabled={!isDirty || isSubmitting || isSaving}
              isLoading={isSubmitting || isSaving}
            loadingText="Saving…"
          >
            Save
          </Button>
          {savedMessage ? (
            <span
              data-testid="brand-saved-message"
              aria-live="polite"
              className="text-xs text-muted-foreground transition-opacity duration-300 opacity-100"
            >
              Saved
            </span>
          ) : null}
        </div>
      </form>
    </Card>
  );
}

import { useAuth } from "@clerk/tanstack-react-start";
import { useNavigate } from "@tanstack/react-router";
import { Card } from "@citetrack/ui/card";
import { useState } from "react";
import type { OnboardingData } from "../lib/schema";
import { submitOnboarding } from "#/features/onboarding/lib/submit";
import { researchCompetitors } from "#/features/onboarding/lib/research";
import { StepIndicator } from "../components/step-indicator";
import { BrandStep } from "../steps/brand-step";
import { CompetitorsStep } from "../steps/competitors-step";
import type { ResearchState } from "../steps/competitors-step";
import { EnginesStep } from "../steps/engines-step";
import { DoneStep } from "../steps/done-step";

export function OnboardingPage() {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [data, setData] = useState<Partial<OnboardingData>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [researchState, setResearchState] = useState<ResearchState>({ status: "idle" });

  const { getToken } = useAuth();
  const navigate = useNavigate();

  const runSubmit = async (finalData: OnboardingData) => {
    setSubmitting(true);
    setError(null);
    try {
      await submitOnboarding(finalData, getToken);
      setSubmitting(false);
      setTimeout(() => {
        void navigate({ to: "/dashboard" });
      }, 1500);
    } catch (err) {
      setSubmitting(false);
      setError(err instanceof Error ? err.message : "Something went wrong");
    }
  };

  const handleBrandNext = async (brand: OnboardingData["brand"]) => {
    setData((prev) => ({ ...prev, brand }));
    setStep(2);
    setResearchState({ status: "loading" });
    try {
      const result = await researchCompetitors({ domain: brand.domain, getToken });
      if (result.degraded) {
        setResearchState({
          status: "degraded",
          reason: result.degraded.reason,
          message: result.degraded.message,
        });
      } else if (result.competitors.length === 0) {
        setResearchState({ status: "success", competitors: [] });
      } else {
        setResearchState({ status: "success", competitors: result.competitors });
        setData((d) => ({ ...d, competitors: result.competitors }));
      }
    } catch (err) {
      setResearchState({
        status: "error",
        message: err instanceof Error ? err.message : "Research failed",
      });
    }
  };

  const handleCompetitorsNext = (competitors: OnboardingData["competitors"]) => {
    setData((prev) => ({ ...prev, competitors }));
    setStep(3);
  };

  const handleEnginesNext = (engines: OnboardingData["engines"]) => {
    const merged = { ...data, engines };
    setData(merged);
    setStep(4);
    void runSubmit(merged as OnboardingData);
  };

  const handleBack = () => {
    if (step === 2) setStep(1);
    else if (step === 3) setStep(2);
  };

  const handleRetry = () => {
    void runSubmit(data as OnboardingData);
  };

  return (
    <main className="flex-1 overflow-auto bg-background">
      <div className="mx-auto max-w-2xl space-y-8 px-4 py-12">
        <StepIndicator current={step} total={4} />
        <Card className="p-6">
          {step === 1 && (
            <BrandStep onNext={handleBrandNext} initial={data.brand} />
          )}
          {step === 2 && (
            <CompetitorsStep
              onNext={handleCompetitorsNext}
              onBack={handleBack}
              initial={data.competitors}
              researchState={researchState}
            />
          )}
          {step === 3 && (
            <EnginesStep
              onNext={handleEnginesNext}
              onBack={handleBack}
              initial={data.engines}
            />
          )}
          {step === 4 && (
            <DoneStep
              submitting={submitting}
              error={error}
              onRetry={handleRetry}
            />
          )}
        </Card>
      </div>
    </main>
  );
}

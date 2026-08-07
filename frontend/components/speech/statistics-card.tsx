import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { countWords, formatDuration } from "@/lib/utils";

interface StatisticsCardProps {
  transcript: string;
  durationSeconds: number;
  model: string | null;
  language: string | null;
  isRefining: boolean;
  wasRefined: boolean;
}

function countSentences(text: string): number {
  const matches = text.match(/[.!?]+(?=\s|$)/g);
  return matches ? matches.length : text.trim() ? 1 : 0;
}

export function StatisticsCard({
  transcript,
  durationSeconds,
  model,
  language,
  isRefining,
  wasRefined,
}: StatisticsCardProps) {
  const words = countWords(transcript);
  const characters = transcript.length;
  const sentences = countSentences(transcript);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>Statistics</CardTitle>
        {isRefining && <Badge variant="info">Refining…</Badge>}
        {!isRefining && wasRefined && <Badge variant="success">Refined</Badge>}
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Stat label="Words" value={words} />
        <Stat label="Characters" value={characters} />
        <Stat label="Sentences" value={sentences} />
        <Stat label="Duration" value={formatDuration(durationSeconds)} />
        <Stat label="Language" value={language?.toUpperCase() ?? "—"} />
        <Stat label="Model" value={model ?? "—"} />
      </CardContent>
    </Card>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-caption uppercase tracking-wide text-muted-foreground/70">{label}</p>
      <p className="font-medium text-foreground">{value}</p>
    </div>
  );
}

export interface RagSource {
  filename: string;
  page: number;
  score: number;
  snippet: string;
}

export interface RagChatResponse {
  success: true;
  answer: string;
  found: boolean;
  sources: RagSource[];
}

"use client";

import * as React from "react";

/**
 * Tracks which document the document assistant is allowed to answer about.
 *
 * The assistant is mounted globally in the root layout, but retrieval is scoped
 * server-side to a single `document_id` — so the OCR view has to publish the id
 * of the document currently on screen, and the widget reads it from here. When
 * this is `null` the assistant has nothing to answer about and says so instead
 * of silently searching some other document.
 */
export interface ActiveDocument {
  documentId: string;
  filename: string;
}

interface ActiveDocumentContextValue {
  document: ActiveDocument | null;
  setDocument: (document: ActiveDocument | null) => void;
}

const ActiveDocumentContext =
  React.createContext<ActiveDocumentContextValue | null>(null);

export function ActiveDocumentProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [document, setDocument] = React.useState<ActiveDocument | null>(null);
  const value = React.useMemo(() => ({ document, setDocument }), [document]);

  return (
    <ActiveDocumentContext.Provider value={value}>
      {children}
    </ActiveDocumentContext.Provider>
  );
}

export function useActiveDocument(): ActiveDocumentContextValue {
  const context = React.useContext(ActiveDocumentContext);
  if (!context) {
    throw new Error(
      "useActiveDocument must be used inside <ActiveDocumentProvider>"
    );
  }
  return context;
}

export class TemplatingPreviewAvailableDoc {
  id: number
  title: string
}

export class TemplatingPreviewAvailableDocs {
  DocsForPreview: TemplatingPreviewAvailableDoc[]
}

export enum TemplatingPreviewResultStatus {
  OK = 'OK',
  FAILED = 'FAILED',
}

export interface TemplatingPreviewResult {
  debug_string?: string
  preview?: string

  input?: string
  doc_id?: number

  result?: TemplatingPreviewResultStatus

  errors?: Array<string>
  warnings?: Array<string>
}

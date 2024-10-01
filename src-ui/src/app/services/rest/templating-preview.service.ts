import { HttpClient } from '@angular/common/http'
import { Injectable } from '@angular/core'
import { map, Observable } from 'rxjs'
import {
  TemplatingPreviewAvailableDoc,
  TemplatingPreviewAvailableDocs,
  TemplatingPreviewResult,
} from 'src/app/data/templating-preview-models'
import { environment } from 'src/environments/environment'

@Injectable({
  providedIn: 'root',
})
export class TemplatingPreviewService {
  constructor(private http: HttpClient) {}

  getDocsForPreview(): Observable<TemplatingPreviewAvailableDoc[]> {
    return this.http.get(`${environment.apiBaseUrl}templating_preview/`).pipe(
      map((res) => {
        let result: TemplatingPreviewAvailableDoc[] = []
        res['DocsForPreview'].forEach((element) => {
          let newEntry: TemplatingPreviewAvailableDoc =
            new TemplatingPreviewAvailableDoc()
          newEntry.id = element[0]
          newEntry.title = element[1]
          result.push(newEntry)
        })

        return result
      })
    )
  }

  requestPreview(
    template: string,
    selectedPreviewDocumentId: number | null,
    removeNewLines: boolean
  ): Observable<TemplatingPreviewResult> {
    let body: { template: string; remove_new_lines?: boolean; doc_id?: number }

    if (selectedPreviewDocumentId == null) {
      body = { template: template, remove_new_lines: removeNewLines }
    } else {
      body = {
        template: template,
        doc_id: selectedPreviewDocumentId,
        remove_new_lines: removeNewLines,
      }
    }

    return this.http.post<TemplatingPreviewResult>(
      `${environment.apiBaseUrl}templating_preview/`,
      body
    )
  }
}

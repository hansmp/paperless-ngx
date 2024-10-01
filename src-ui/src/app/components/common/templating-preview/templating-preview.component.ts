import {
  Component,
  Input,
  OnChanges,
  OnInit,
  SimpleChanges,
} from '@angular/core'
import { Observable, of } from 'rxjs'
import {
  TemplatingPreviewAvailableDoc,
  TemplatingPreviewResult,
} from 'src/app/data/templating-preview-models'
import { TemplatingPreviewService } from 'src/app/services/rest/templating-preview.service'

@Component({
  selector: 'pngx-templating-preview',
  templateUrl: './templating-preview.component.html',
  styleUrl: './templating-preview.component.scss',
})
export class TemplatingPreviewComponent implements OnInit, OnChanges {
  @Input({ required: true }) template: string

  availableDocsForPreview: TemplatingPreviewAvailableDoc[] = null
  selectedPreviewDocumentId: number | null = null

  enableTemplatePreview: boolean = false
  templatePreviewResult: TemplatingPreviewResult | null = null

  constructor(private templatingPreviewService: TemplatingPreviewService) {}

  ngOnInit(): void {
    this.templatingPreviewService.getDocsForPreview().subscribe((res) => {
      this.availableDocsForPreview = res
    })
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes?.template != null) {
      this.requestTemplatePreviewUpdate()
    }
  }

  getOpenPreviewTitle() {
    return $localize`Template live preview`
  }

  requestTemplatePreviewUpdate() {
    if (this.enableTemplatePreview == false) return
    this.templatingPreviewService
      .requestPreview(this.template, this.selectedPreviewDocumentId, true)
      .subscribe((x) => {
        this.templatePreviewResult = x
      })
  }
}

import { ComponentFixture, TestBed } from '@angular/core/testing'

import { TemplatingPreviewComponent } from './templating-preview.component'

describe('TemplatingPreviewComponent', () => {
  let component: TemplatingPreviewComponent
  let fixture: ComponentFixture<TemplatingPreviewComponent>

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TemplatingPreviewComponent],
    }).compileComponents()

    fixture = TestBed.createComponent(TemplatingPreviewComponent)
    component = fixture.componentInstance
    fixture.detectChanges()
  })

  it('should create', () => {
    expect(component).toBeTruthy()
  })
})

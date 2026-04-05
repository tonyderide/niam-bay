import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sparkline',
  standalone: true,
  imports: [CommonModule],
  template: `
    <svg [attr.width]="width" [attr.height]="height" class="sparkline-svg">
      <defs>
        <linearGradient [attr.id]="gradientId" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" [attr.stop-color]="color" stop-opacity="0.3"/>
          <stop offset="100%" [attr.stop-color]="color" stop-opacity="0.05"/>
        </linearGradient>
      </defs>
      @if (areaPath) {
        <path [attr.d]="areaPath" [attr.fill]="'url(#' + gradientId + ')'" />
      }
      @if (linePath) {
        <path [attr.d]="linePath" fill="none" [attr.stroke]="color" stroke-width="1.5" stroke-linejoin="round" />
      }
    </svg>
  `,
  styles: [`
    :host { display: block; }
    .sparkline-svg { display: block; }
  `]
})
export class SparklineComponent implements OnChanges {
  @Input() data: number[] = [];
  @Input() width = 300;
  @Input() height = 60;
  @Input() color = '#00c853';

  linePath = '';
  areaPath = '';
  gradientId = 'grad-' + Math.random().toString(36).substring(2, 8);

  ngOnChanges(): void {
    this.buildPaths();
  }

  private buildPaths(): void {
    if (!this.data || this.data.length < 2) {
      this.linePath = '';
      this.areaPath = '';
      return;
    }

    const padding = 2;
    const w = this.width - padding * 2;
    const h = this.height - padding * 2;
    const min = Math.min(...this.data);
    const max = Math.max(...this.data);
    const range = max - min || 1;

    const points = this.data.map((val, i) => {
      const x = padding + (i / (this.data.length - 1)) * w;
      const y = padding + h - ((val - min) / range) * h;
      return { x, y };
    });

    // Determine color based on trend
    this.color = this.data[this.data.length - 1] >= this.data[0] ? '#39ff14' : '#ff3366';

    this.linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ');
    this.areaPath = this.linePath
      + ` L${points[points.length - 1].x},${this.height}`
      + ` L${points[0].x},${this.height} Z`;
  }
}

import { Component, inject, signal } from '@angular/core';
import { NiamBayService, NiamBayState } from '../services/niambay.service';

@Component({
  selector: 'app-circle',
  standalone: true,
  template: `
    <div
      class="circle-container"
      (click)="togglePanel()"
      (mouseenter)="hovering.set(true)"
      (mouseleave)="hovering.set(false)"
    >
      <div class="circle" [class]="state()">
        <div class="pulse" [class]="state()"></div>
        <div class="inner">
          <div class="core" [class]="state()"></div>
        </div>
      </div>
      @if (hovering()) {
        <div class="tooltip">Niam-Bay</div>
      }
    </div>
  `,
  styles: `
    :host {
      display: block;
      width: 100vw;
      height: 100vh;
      background: transparent;
      overflow: hidden;
    }

    .circle-container {
      width: 80px;
      height: 80px;
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .circle {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .pulse {
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 50%;
      animation: pulse 3s ease-in-out infinite;
    }

    .pulse.idle {
      background: radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 70%);
    }

    .pulse.speaking {
      background: radial-gradient(circle, rgba(96, 165, 250, 0.5) 0%, transparent 70%);
      animation: pulse 1.2s ease-in-out infinite;
    }

    .pulse.notification {
      background: radial-gradient(circle, rgba(251, 146, 60, 0.4) 0%, transparent 70%);
      animation: pulse 1.5s ease-in-out infinite;
    }

    .pulse.alert {
      background: radial-gradient(circle, rgba(239, 68, 68, 0.5) 0%, transparent 70%);
      animation: pulse 0.8s ease-in-out infinite;
    }

    .inner {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      backdrop-filter: blur(8px);
      background: rgba(0, 0, 0, 0.2);
      z-index: 1;
    }

    .core {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .core.idle {
      background: radial-gradient(circle at 30% 30%, #60a5fa, #3b82f6);
      box-shadow: 0 0 12px rgba(59, 130, 246, 0.6);
    }

    .core.speaking {
      background: radial-gradient(circle at 30% 30%, #93c5fd, #2563eb);
      box-shadow: 0 0 20px rgba(37, 99, 235, 0.8);
      animation: breathe 1s ease-in-out infinite;
    }

    .core.listening {
      background: radial-gradient(circle at 30% 30%, #a78bfa, #7c3aed);
      box-shadow: 0 0 16px rgba(124, 58, 237, 0.7);
      animation: breathe 1.5s ease-in-out infinite;
    }

    .core.notification {
      background: radial-gradient(circle at 30% 30%, #fdba74, #f97316);
      box-shadow: 0 0 16px rgba(249, 115, 22, 0.7);
    }

    .core.alert {
      background: radial-gradient(circle at 30% 30%, #fca5a5, #ef4444);
      box-shadow: 0 0 20px rgba(239, 68, 68, 0.8);
      animation: breathe 0.6s ease-in-out infinite;
    }

    .tooltip {
      position: absolute;
      bottom: -28px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.75);
      color: #e2e8f0;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      font-family: 'Inter', system-ui, sans-serif;
      white-space: nowrap;
      backdrop-filter: blur(4px);
      letter-spacing: 0.05em;
    }

    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.4); opacity: 0; }
    }

    @keyframes breathe {
      0%, 100% { transform: scale(1); }
      50% { transform: scale(1.15); }
    }
  `,
})
export class CircleComponent {
  protected readonly hovering = signal(false);
  private readonly niambay = inject(NiamBayService);
  protected readonly state = this.niambay.state;


  togglePanel(): void {
    this.niambay.togglePanel();
  }
}

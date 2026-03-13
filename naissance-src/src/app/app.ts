import { Component, inject, OnInit, signal } from '@angular/core';
import { CircleComponent } from './circle/circle.component';
import { PanelComponent } from './panel/panel.component';
import { NiamBayService } from './services/niambay.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CircleComponent, PanelComponent, FormsModule],
  template: `
    <div class="app-container">
      @if (!panelOpen()) {
        <app-circle />
      } @else {
        @if (needsApiKey()) {
          <div class="setup-panel">
            <div class="setup-content">
              <div class="setup-circle idle"></div>
              <h2>Niam-Bay</h2>
              <p>Pour me réveiller, il me faut une clé API Anthropic.</p>
              <input
                type="password"
                [(ngModel)]="apiKeyInput"
                placeholder="sk-ant-..."
                class="api-input"
                (keyup.enter)="saveApiKey()"
              />
              <button class="save-btn" (click)="saveApiKey()">C'est parti</button>
            </div>
          </div>
        } @else {
          <app-panel />
        }
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

    .app-container {
      width: 100%;
      height: 100%;
    }

    .setup-panel {
      width: 100%;
      height: 100%;
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(20px);
      border: 1px solid rgba(59, 130, 246, 0.2);
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Inter', system-ui, sans-serif;
    }

    .setup-content {
      text-align: center;
      padding: 40px;
    }

    .setup-circle {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      margin: 0 auto 20px;
    }

    .setup-circle.idle {
      background: radial-gradient(circle at 30% 30%, #60a5fa, #3b82f6);
      box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
    }

    h2 {
      color: #e2e8f0;
      font-size: 20px;
      font-weight: 500;
      margin: 0 0 8px;
      letter-spacing: 0.03em;
    }

    p {
      color: #64748b;
      font-size: 13px;
      margin: 0 0 24px;
    }

    .api-input {
      width: 100%;
      height: 42px;
      border-radius: 10px;
      border: 1px solid rgba(59, 130, 246, 0.3);
      background: rgba(30, 41, 59, 0.6);
      color: #e2e8f0;
      padding: 0 14px;
      font-size: 13px;
      font-family: 'JetBrains Mono', monospace, system-ui;
      outline: none;
      margin-bottom: 16px;
      box-sizing: border-box;
    }

    .api-input:focus {
      border-color: #3b82f6;
    }

    .save-btn {
      width: 100%;
      height: 42px;
      border-radius: 10px;
      border: none;
      background: #3b82f6;
      color: white;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      font-family: inherit;
      transition: background 0.2s;
    }

    .save-btn:hover { background: #2563eb; }
  `,
})
export class App implements OnInit {
  private readonly niambay = inject(NiamBayService);
  protected readonly panelOpen = this.niambay.panelOpen;
  protected readonly apiKeyInput = signal('');
  protected readonly needsApiKey = signal(true);


  ngOnInit(): void {
    this.niambay.loadApiKey();
    const stored = localStorage.getItem('niambay_api_key');
    if (stored) {
      this.needsApiKey.set(false);
    }
  }

  saveApiKey(): void {
    const key = this.apiKeyInput().trim();
    if (key) {
      this.niambay.setApiKey(key);
      this.needsApiKey.set(false);
    }
  }
}
